/**
 * Tests for FreemiumForecastClient — two-step verify+forecast contract.
 *
 * Requirements under test:
 *   HP1 — base URL is https://forecasting.api.asoba.org (not the old api.asoba.org)
 *   HP2 — requestVerificationCode() POSTs to /api/v1/freemium-forecast/verify with email
 *   HP3 — getForecast() POSTs multipart/form-data to /api/v1/freemium-forecast with all
 *          six required fields: email, verification_code, site_name, location, capacity_kw, file
 *   EC1 — missing CSV file throws ValidationError (existing behaviour preserved)
 *   EC2 — invalid / missing email throws ValidationError (existing behaviour preserved)
 *   EC3 — missing verification_code throws ValidationError
 *   EC4 — missing capacity_kw throws ValidationError
 *   EH1 — server 400 "Missing required fields" rejects with ValidationError
 *   EH2 — server 500 rejects with ServiceUnavailableError
 *   INV1 — no request ever reaches the old api.asoba.org domain
 *
 * NEW — Terms of Use and marketing opt-in contract (live API requirement):
 *   TOU-HP1 — getForecast with touAccepted:true sends multipart field tou_accepted="true"
 *   TOU-EC1 — getForecast without touAccepted (omitted) throws ValidationError before any
 *             network call
 *   TOU-EC2 — getForecast with touAccepted:false throws ValidationError before any network
 *             call (client must not silently coerce false → "true")
 *   TOU-EC3 — getForecast with touAccepted:null throws ValidationError before any network
 *             call
 *   MKT-HP1 — getForecast with marketingOptIn:true sends marketing_opt_in="true"
 *   MKT-EC1 — getForecast without marketingOptIn (omitted) does NOT send
 *             marketing_opt_in="true" (field absent or "false" — defaults to not-opted-in)
 *   MKT-EC2 — getForecast with marketingOptIn:false sends marketing_opt_in="false"
 *   EH-TOU1 — server 400 "Terms of Use" error surfaces in ValidationError message
 */

'use strict';

const http = require('http');
const os = require('os');
const fs = require('fs');
const path = require('path');
const { FreemiumForecastClient, ServiceUnavailableError } = require('../src/services/FreemiumForecastClient');
const { ValidationError } = require('../src/utils/errors');

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Start a local plain-HTTP server. Returns { server, port, close(), lastReq }. */
function startServer(handler) {
  return new Promise((resolve) => {
    const state = { lastReq: null };
    const server = http.createServer((req, res) => {
      // Collect full body so assertions can parse multipart payload
      let body = Buffer.alloc(0);
      req.on('data', (chunk) => { body = Buffer.concat([body, chunk]); });
      req.on('end', () => {
        state.lastReq = { method: req.method, url: req.url, headers: req.headers, body };
        handler(req, res, body);
      });
    });
    server.listen(0, '127.0.0.1', () => {
      const { port } = server.address();
      resolve({
        server,
        port,
        state,
        close: () => new Promise(res => server.close(res)),
      });
    });
  });
}

/** Create a FreemiumForecastClient whose internal URL points at a local HTTP server. */
function makeTestClient(port) {
  const client = new FreemiumForecastClient({});
  // Override the private URL to redirect all calls to our local server
  client._url = `http://127.0.0.1:${port}/api/v1/freemium-forecast`;
  return client;
}

/** Write a temporary CSV file and return its path. Cleaned up after the test. */
function makeTempCsv(content = 'timestamp,power_kw\n2026-01-01T00:00:00,1.5\n') {
  const tmpPath = path.join(os.tmpdir(), `test-forecast-${Date.now()}.csv`);
  fs.writeFileSync(tmpPath, content);
  return tmpPath;
}

// Default success response the server sends back
const SUCCESS_RESPONSE = {
  forecast: {
    forecasts: [{ timestamp: '2026-01-02T00:00:00', kWh_forecast: 12.5 }],
    summary: { total_kWh: 12.5 },
  },
};

// ---------------------------------------------------------------------------
// HP1 — client targets forecasting.api.asoba.org, NOT the old api.asoba.org
// ---------------------------------------------------------------------------

describe('HP1 — base URL is forecasting.api.asoba.org', () => {
  test('HP1a default _url starts with https://forecasting.api.asoba.org', () => {
    const client = new FreemiumForecastClient({});
    expect(client._url).toMatch(/^https:\/\/forecasting\.api\.asoba\.org/);
  });

  test('HP1b default _url does NOT contain the old api.asoba.org/v1 path', () => {
    const client = new FreemiumForecastClient({});
    // The old URL was https://api.asoba.org/v1/freemium-forecast
    expect(client._url).not.toMatch(/api\.asoba\.org\/v1/);
  });
});

// ---------------------------------------------------------------------------
// HP2 — requestVerificationCode() exists and POSTs to the /verify path
// ---------------------------------------------------------------------------

describe('HP2 — requestVerificationCode posts to /verify', () => {
  let srv;

  beforeAll(async () => {
    srv = await startServer((req, res) => {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ message: 'Verification code sent' }));
    });
  });

  afterAll(() => srv.close());

  test('HP2a requestVerificationCode method exists', () => {
    const client = new FreemiumForecastClient({});
    expect(typeof client.requestVerificationCode).toBe('function');
  });

  test('HP2b requestVerificationCode sends POST to /api/v1/freemium-forecast/verify', async () => {
    const client = makeTestClient(srv.port);
    // Override specifically the verify URL if the client uses a separate property,
    // or expect the method to append /verify to the base forecast URL.
    // Either way, the outgoing request must hit the /verify path.
    await client.requestVerificationCode({ email: 'user@example.com' });
    expect(srv.state.lastReq.method).toBe('POST');
    expect(srv.state.lastReq.url).toBe('/api/v1/freemium-forecast/verify');
  });

  test('HP2c requestVerificationCode body contains the email', async () => {
    const client = makeTestClient(srv.port);
    await client.requestVerificationCode({ email: 'user@example.com' });
    const body = srv.state.lastReq.body.toString();
    expect(body).toContain('user@example.com');
  });
});

// ---------------------------------------------------------------------------
// HP3 — getForecast POSTs multipart to /api/v1/freemium-forecast with all 6 fields
// ---------------------------------------------------------------------------

describe('HP3 — getForecast posts all six required fields', () => {
  let srv;
  let csvPath;

  beforeAll(async () => {
    srv = await startServer((req, res) => {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(SUCCESS_RESPONSE));
    });
    csvPath = makeTempCsv();
  });

  afterAll(async () => {
    await srv.close();
    if (fs.existsSync(csvPath)) fs.unlinkSync(csvPath);
  });

  test('HP3a getForecast hits path /api/v1/freemium-forecast', async () => {
    const client = makeTestClient(srv.port);
    await client.getForecast({
      csvPath,
      email: 'user@example.com',
      siteName: 'Test Site',
      location: 'Durban',
      verificationCode: '123456',
      capacityKw: 10.0,
      touAccepted: true,
    });
    expect(srv.state.lastReq.url).toBe('/api/v1/freemium-forecast');
  });

  test('HP3b getForecast uses POST method', async () => {
    const client = makeTestClient(srv.port);
    await client.getForecast({
      csvPath,
      email: 'user@example.com',
      siteName: 'Test Site',
      location: 'Durban',
      verificationCode: '123456',
      capacityKw: 10.0,
      touAccepted: true,
    });
    expect(srv.state.lastReq.method).toBe('POST');
  });

  test('HP3c getForecast sends multipart/form-data content-type', async () => {
    const client = makeTestClient(srv.port);
    await client.getForecast({
      csvPath,
      email: 'user@example.com',
      siteName: 'Test Site',
      location: 'Durban',
      verificationCode: '123456',
      capacityKw: 10.0,
      touAccepted: true,
    });
    expect(srv.state.lastReq.headers['content-type']).toMatch(/multipart\/form-data/);
  });

  test('HP3d multipart body contains "email" field', async () => {
    const client = makeTestClient(srv.port);
    await client.getForecast({
      csvPath,
      email: 'user@example.com',
      siteName: 'Test Site',
      location: 'Durban',
      verificationCode: '123456',
      capacityKw: 10.0,
      touAccepted: true,
    });
    const body = srv.state.lastReq.body.toString();
    expect(body).toContain('name="email"');
    expect(body).toContain('user@example.com');
  });

  test('HP3e multipart body contains "verification_code" field', async () => {
    const client = makeTestClient(srv.port);
    await client.getForecast({
      csvPath,
      email: 'user@example.com',
      siteName: 'Test Site',
      location: 'Durban',
      verificationCode: '123456',
      capacityKw: 10.0,
      touAccepted: true,
    });
    const body = srv.state.lastReq.body.toString();
    expect(body).toContain('name="verification_code"');
    expect(body).toContain('123456');
  });

  test('HP3f multipart body contains "site_name" field', async () => {
    const client = makeTestClient(srv.port);
    await client.getForecast({
      csvPath,
      email: 'user@example.com',
      siteName: 'Test Site',
      location: 'Durban',
      verificationCode: '123456',
      capacityKw: 10.0,
      touAccepted: true,
    });
    const body = srv.state.lastReq.body.toString();
    expect(body).toContain('name="site_name"');
    expect(body).toContain('Test Site');
  });

  test('HP3g multipart body contains "location" field', async () => {
    const client = makeTestClient(srv.port);
    await client.getForecast({
      csvPath,
      email: 'user@example.com',
      siteName: 'Test Site',
      location: 'Durban',
      verificationCode: '123456',
      capacityKw: 10.0,
      touAccepted: true,
    });
    const body = srv.state.lastReq.body.toString();
    expect(body).toContain('name="location"');
    expect(body).toContain('Durban');
  });

  test('HP3h multipart body contains "capacity_kw" field', async () => {
    const client = makeTestClient(srv.port);
    await client.getForecast({
      csvPath,
      email: 'user@example.com',
      siteName: 'Test Site',
      location: 'Durban',
      verificationCode: '123456',
      capacityKw: 10.0,
      touAccepted: true,
    });
    const body = srv.state.lastReq.body.toString();
    expect(body).toContain('name="capacity_kw"');
    expect(body).toContain('10');
  });

  test('HP3i multipart body contains "file" field with CSV content', async () => {
    const client = makeTestClient(srv.port);
    await client.getForecast({
      csvPath,
      email: 'user@example.com',
      siteName: 'Test Site',
      location: 'Durban',
      verificationCode: '123456',
      capacityKw: 10.0,
      touAccepted: true,
    });
    const body = srv.state.lastReq.body.toString();
    expect(body).toContain('name="file"');
    expect(body).toContain('timestamp,power_kw');
  });

  test('HP3j successful response resolves with parsed JSON', async () => {
    const client = makeTestClient(srv.port);
    const result = await client.getForecast({
      csvPath,
      email: 'user@example.com',
      siteName: 'Test Site',
      location: 'Durban',
      verificationCode: '123456',
      capacityKw: 10.0,
      touAccepted: true,
    });
    expect(result).toEqual(SUCCESS_RESPONSE);
  });
});

// ---------------------------------------------------------------------------
// EC1 — missing / nonexistent CSV file → ValidationError (existing behaviour)
// ---------------------------------------------------------------------------

describe('EC1 — missing CSV file throws ValidationError', () => {
  test('EC1a nonexistent path throws ValidationError', async () => {
    const client = new FreemiumForecastClient({});
    await expect(
      client.getForecast({
        csvPath: '/tmp/does-not-exist-99999999.csv',
        email: 'user@example.com',
        siteName: 'Site',
        location: 'Loc',
        verificationCode: '000000',
        capacityKw: 5.0,
      })
    ).rejects.toThrow(ValidationError);
  });

  test('EC1b null csvPath throws ValidationError', async () => {
    const client = new FreemiumForecastClient({});
    await expect(
      client.getForecast({
        csvPath: null,
        email: 'user@example.com',
        siteName: 'Site',
        location: 'Loc',
        verificationCode: '000000',
        capacityKw: 5.0,
      })
    ).rejects.toThrow(ValidationError);
  });
});

// ---------------------------------------------------------------------------
// EC2 — invalid / missing email → ValidationError (existing behaviour)
// ---------------------------------------------------------------------------

describe('EC2 — invalid email throws ValidationError', () => {
  let csvPath;
  beforeAll(() => { csvPath = makeTempCsv(); });
  afterAll(() => { if (fs.existsSync(csvPath)) fs.unlinkSync(csvPath); });

  test('EC2a email without @ throws ValidationError', async () => {
    const client = new FreemiumForecastClient({});
    await expect(
      client.getForecast({
        csvPath,
        email: 'notanemail',
        siteName: 'Site',
        location: 'Loc',
        verificationCode: '000000',
        capacityKw: 5.0,
      })
    ).rejects.toThrow(ValidationError);
  });

  test('EC2b null email throws ValidationError', async () => {
    const client = new FreemiumForecastClient({});
    await expect(
      client.getForecast({
        csvPath,
        email: null,
        siteName: 'Site',
        location: 'Loc',
        verificationCode: '000000',
        capacityKw: 5.0,
      })
    ).rejects.toThrow(ValidationError);
  });
});

// ---------------------------------------------------------------------------
// EC3 — missing verification_code → ValidationError (new requirement)
// ---------------------------------------------------------------------------

describe('EC3 — missing verificationCode throws ValidationError', () => {
  let csvPath;
  beforeAll(() => { csvPath = makeTempCsv(); });
  afterAll(() => { if (fs.existsSync(csvPath)) fs.unlinkSync(csvPath); });

  test('EC3a omitted verificationCode throws ValidationError before any network call', async () => {
    const client = new FreemiumForecastClient({});
    await expect(
      client.getForecast({
        csvPath,
        email: 'user@example.com',
        siteName: 'Site',
        location: 'Loc',
        // verificationCode intentionally omitted
        capacityKw: 5.0,
      })
    ).rejects.toThrow(ValidationError);
  });

  test('EC3b empty string verificationCode throws ValidationError', async () => {
    const client = new FreemiumForecastClient({});
    await expect(
      client.getForecast({
        csvPath,
        email: 'user@example.com',
        siteName: 'Site',
        location: 'Loc',
        verificationCode: '',
        capacityKw: 5.0,
      })
    ).rejects.toThrow(ValidationError);
  });
});

// ---------------------------------------------------------------------------
// EC4 — missing capacity_kw → ValidationError (new requirement)
// ---------------------------------------------------------------------------

describe('EC4 — missing capacityKw throws ValidationError', () => {
  let csvPath;
  beforeAll(() => { csvPath = makeTempCsv(); });
  afterAll(() => { if (fs.existsSync(csvPath)) fs.unlinkSync(csvPath); });

  test('EC4a omitted capacityKw throws ValidationError before any network call', async () => {
    const client = new FreemiumForecastClient({});
    await expect(
      client.getForecast({
        csvPath,
        email: 'user@example.com',
        siteName: 'Site',
        location: 'Loc',
        verificationCode: '123456',
        // capacityKw intentionally omitted
      })
    ).rejects.toThrow(ValidationError);
  });

  test('EC4b null capacityKw throws ValidationError', async () => {
    const client = new FreemiumForecastClient({});
    await expect(
      client.getForecast({
        csvPath,
        email: 'user@example.com',
        siteName: 'Site',
        location: 'Loc',
        verificationCode: '123456',
        capacityKw: null,
      })
    ).rejects.toThrow(ValidationError);
  });
});

// ---------------------------------------------------------------------------
// EH1 — server 400 "Missing required fields" → ValidationError
// ---------------------------------------------------------------------------

describe('EH1 — HTTP 400 from server rejects with ValidationError', () => {
  let srv;
  let csvPath;

  beforeAll(async () => {
    srv = await startServer((req, res) => {
      res.writeHead(400, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Missing required fields: verification_code, capacity_kw' }));
    });
    csvPath = makeTempCsv();
  });

  afterAll(async () => {
    await srv.close();
    if (fs.existsSync(csvPath)) fs.unlinkSync(csvPath);
  });

  test('EH1a server 400 rejects with ValidationError', async () => {
    const client = makeTestClient(srv.port);
    await expect(
      client.getForecast({
        csvPath,
        email: 'user@example.com',
        siteName: 'Site',
        location: 'Loc',
        verificationCode: '123456',
        capacityKw: 5.0,
        touAccepted: true,
      })
    ).rejects.toThrow(ValidationError);
  });

  test('EH1b ValidationError message surfaces the server error text', async () => {
    const client = makeTestClient(srv.port);
    let caught;
    try {
      await client.getForecast({
        csvPath,
        email: 'user@example.com',
        siteName: 'Site',
        location: 'Loc',
        verificationCode: '123456',
        capacityKw: 5.0,
        touAccepted: true,
      });
    } catch (e) {
      caught = e;
    }
    expect(caught).toBeInstanceOf(ValidationError);
    expect(caught.message).toMatch(/Missing required fields/);
  });
});

// ---------------------------------------------------------------------------
// EH2 — server 500 → ServiceUnavailableError
// ---------------------------------------------------------------------------

describe('EH2 — HTTP 500 from server rejects with ServiceUnavailableError', () => {
  let srv;
  let csvPath;

  beforeAll(async () => {
    srv = await startServer((req, res) => {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Internal server error' }));
    });
    csvPath = makeTempCsv();
  });

  afterAll(async () => {
    await srv.close();
    if (fs.existsSync(csvPath)) fs.unlinkSync(csvPath);
  });

  test('EH2 server 500 rejects with ServiceUnavailableError', async () => {
    const client = makeTestClient(srv.port);
    await expect(
      client.getForecast({
        csvPath,
        email: 'user@example.com',
        siteName: 'Site',
        location: 'Loc',
        verificationCode: '123456',
        capacityKw: 5.0,
        touAccepted: true,
      })
    ).rejects.toThrow(ServiceUnavailableError);
  });
});

// ---------------------------------------------------------------------------
// INV1 — the old endpoint string must not appear anywhere in the client at runtime
// ---------------------------------------------------------------------------

describe('INV1 — old endpoint is not referenced at runtime', () => {
  test('INV1 freshly constructed client _url does not contain api.asoba.org/v1', () => {
    const client = new FreemiumForecastClient({});
    // The old URL was https://api.asoba.org/v1/freemium-forecast
    expect(client._url).not.toContain('api.asoba.org/v1');
  });
});

// ---------------------------------------------------------------------------
// TOU-HP1 — touAccepted:true sends tou_accepted="true" in the multipart body
// ---------------------------------------------------------------------------

describe('TOU-HP1 — tou_accepted field is sent as "true" when caller accepts', () => {
  let srv;
  let csvPath;

  beforeAll(async () => {
    srv = await startServer((req, res) => {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(SUCCESS_RESPONSE));
    });
    csvPath = makeTempCsv();
  });

  afterAll(async () => {
    await srv.close();
    if (fs.existsSync(csvPath)) fs.unlinkSync(csvPath);
  });

  test('TOU-HP1a multipart body contains tou_accepted field', async () => {
    const client = makeTestClient(srv.port);
    await client.getForecast({
      csvPath,
      email: 'user@example.com',
      siteName: 'Site',
      location: 'Durban',
      verificationCode: '123456',
      capacityKw: 10.0,
      touAccepted: true,
    });
    const body = srv.state.lastReq.body.toString();
    expect(body).toContain('name="tou_accepted"');
  });

  test('TOU-HP1b tou_accepted field value is the string "true"', async () => {
    const client = makeTestClient(srv.port);
    await client.getForecast({
      csvPath,
      email: 'user@example.com',
      siteName: 'Site',
      location: 'Durban',
      verificationCode: '123456',
      capacityKw: 10.0,
      touAccepted: true,
    });
    const body = srv.state.lastReq.body.toString();
    // The field must appear and its value must be the string "true" (not "1" or "yes")
    // Multipart part: Content-Disposition: form-data; name="tou_accepted"\r\n\r\ntrue
    expect(body).toMatch(/name="tou_accepted"[\s\S]*?true/);
  });
});

// ---------------------------------------------------------------------------
// TOU-EC1 — touAccepted omitted → ValidationError BEFORE any network call
// ---------------------------------------------------------------------------

describe('TOU-EC1 — omitting touAccepted throws ValidationError before any network call', () => {
  let csvPath;
  // Use a server that records whether it was ever contacted — it must NOT be.
  let contactedServer;
  let srv;

  beforeAll(async () => {
    contactedServer = false;
    srv = await startServer((req, res) => {
      contactedServer = true;
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(SUCCESS_RESPONSE));
    });
    csvPath = makeTempCsv();
  });

  afterAll(async () => {
    await srv.close();
    if (fs.existsSync(csvPath)) fs.unlinkSync(csvPath);
  });

  test('TOU-EC1a omitted touAccepted throws ValidationError', async () => {
    const client = makeTestClient(srv.port);
    await expect(
      client.getForecast({
        csvPath,
        email: 'user@example.com',
        siteName: 'Site',
        location: 'Loc',
        verificationCode: '123456',
        capacityKw: 5.0,
        // touAccepted intentionally omitted
      })
    ).rejects.toThrow(ValidationError);
  });

  test('TOU-EC1b no network request is made when touAccepted is omitted', async () => {
    const client = makeTestClient(srv.port);
    contactedServer = false;
    try {
      await client.getForecast({
        csvPath,
        email: 'user@example.com',
        siteName: 'Site',
        location: 'Loc',
        verificationCode: '123456',
        capacityKw: 5.0,
        // touAccepted intentionally omitted
      });
    } catch (_) {
      // expected
    }
    expect(contactedServer).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// TOU-EC2 — touAccepted:false → ValidationError BEFORE any network call
// ---------------------------------------------------------------------------

describe('TOU-EC2 — touAccepted:false throws ValidationError before any network call', () => {
  let csvPath;
  let contactedServer;
  let srv;

  beforeAll(async () => {
    contactedServer = false;
    srv = await startServer((req, res) => {
      contactedServer = true;
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(SUCCESS_RESPONSE));
    });
    csvPath = makeTempCsv();
  });

  afterAll(async () => {
    await srv.close();
    if (fs.existsSync(csvPath)) fs.unlinkSync(csvPath);
  });

  test('TOU-EC2a touAccepted:false throws ValidationError', async () => {
    const client = makeTestClient(srv.port);
    await expect(
      client.getForecast({
        csvPath,
        email: 'user@example.com',
        siteName: 'Site',
        location: 'Loc',
        verificationCode: '123456',
        capacityKw: 5.0,
        touAccepted: false,
      })
    ).rejects.toThrow(ValidationError);
  });

  test('TOU-EC2b no network request is made when touAccepted is false', async () => {
    const client = makeTestClient(srv.port);
    contactedServer = false;
    try {
      await client.getForecast({
        csvPath,
        email: 'user@example.com',
        siteName: 'Site',
        location: 'Loc',
        verificationCode: '123456',
        capacityKw: 5.0,
        touAccepted: false,
      });
    } catch (_) {
      // expected
    }
    expect(contactedServer).toBe(false);
  });
});

// ---------------------------------------------------------------------------
// TOU-EC3 — touAccepted:null → ValidationError BEFORE any network call
// ---------------------------------------------------------------------------

describe('TOU-EC3 — touAccepted:null throws ValidationError before any network call', () => {
  let csvPath;
  beforeAll(() => { csvPath = makeTempCsv(); });
  afterAll(() => { if (fs.existsSync(csvPath)) fs.unlinkSync(csvPath); });

  test('TOU-EC3a touAccepted:null throws ValidationError', async () => {
    const client = new FreemiumForecastClient({});
    await expect(
      client.getForecast({
        csvPath,
        email: 'user@example.com',
        siteName: 'Site',
        location: 'Loc',
        verificationCode: '123456',
        capacityKw: 5.0,
        touAccepted: null,
      })
    ).rejects.toThrow(ValidationError);
  });
});

// ---------------------------------------------------------------------------
// MKT-HP1 — marketingOptIn:true sends marketing_opt_in="true"
// ---------------------------------------------------------------------------

describe('MKT-HP1 — marketingOptIn:true sends marketing_opt_in="true"', () => {
  let srv;
  let csvPath;

  beforeAll(async () => {
    srv = await startServer((req, res) => {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(SUCCESS_RESPONSE));
    });
    csvPath = makeTempCsv();
  });

  afterAll(async () => {
    await srv.close();
    if (fs.existsSync(csvPath)) fs.unlinkSync(csvPath);
  });

  test('MKT-HP1a multipart body contains marketing_opt_in field when opted in', async () => {
    const client = makeTestClient(srv.port);
    await client.getForecast({
      csvPath,
      email: 'user@example.com',
      siteName: 'Site',
      location: 'Durban',
      verificationCode: '123456',
      capacityKw: 10.0,
      touAccepted: true,
      marketingOptIn: true,
    });
    const body = srv.state.lastReq.body.toString();
    expect(body).toContain('name="marketing_opt_in"');
  });

  test('MKT-HP1b marketing_opt_in value is the string "true" when opted in', async () => {
    const client = makeTestClient(srv.port);
    await client.getForecast({
      csvPath,
      email: 'user@example.com',
      siteName: 'Site',
      location: 'Durban',
      verificationCode: '123456',
      capacityKw: 10.0,
      touAccepted: true,
      marketingOptIn: true,
    });
    const body = srv.state.lastReq.body.toString();
    // Multipart part value must be the literal string "true", not "1" or "yes"
    expect(body).toMatch(/name="marketing_opt_in"[\s\S]*?true/);
  });
});

// ---------------------------------------------------------------------------
// MKT-EC1 — marketingOptIn omitted → marketing_opt_in NOT sent as "true"
// ---------------------------------------------------------------------------

describe('MKT-EC1 — omitting marketingOptIn defaults to not-opted-in', () => {
  let srv;
  let csvPath;

  beforeAll(async () => {
    srv = await startServer((req, res) => {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(SUCCESS_RESPONSE));
    });
    csvPath = makeTempCsv();
  });

  afterAll(async () => {
    await srv.close();
    if (fs.existsSync(csvPath)) fs.unlinkSync(csvPath);
  });

  test('MKT-EC1a omitting marketingOptIn does not send marketing_opt_in="true"', async () => {
    const client = makeTestClient(srv.port);
    await client.getForecast({
      csvPath,
      email: 'user@example.com',
      siteName: 'Site',
      location: 'Durban',
      verificationCode: '123456',
      capacityKw: 10.0,
      touAccepted: true,
      // marketingOptIn intentionally omitted
    });
    const body = srv.state.lastReq.body.toString();
    // The body must NOT contain a marketing_opt_in part whose value is "true"
    // (it may be absent entirely, or present as "false" — either is acceptable)
    expect(body).not.toMatch(/name="marketing_opt_in"[\s\S]*?\btrue\b/);
  });
});

// ---------------------------------------------------------------------------
// MKT-EC2 — marketingOptIn:false sends marketing_opt_in="false"
// ---------------------------------------------------------------------------

describe('MKT-EC2 — marketingOptIn:false sends marketing_opt_in="false"', () => {
  let srv;
  let csvPath;

  beforeAll(async () => {
    srv = await startServer((req, res) => {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(SUCCESS_RESPONSE));
    });
    csvPath = makeTempCsv();
  });

  afterAll(async () => {
    await srv.close();
    if (fs.existsSync(csvPath)) fs.unlinkSync(csvPath);
  });

  test('MKT-EC2a marketingOptIn:false sends marketing_opt_in field', async () => {
    const client = makeTestClient(srv.port);
    await client.getForecast({
      csvPath,
      email: 'user@example.com',
      siteName: 'Site',
      location: 'Durban',
      verificationCode: '123456',
      capacityKw: 10.0,
      touAccepted: true,
      marketingOptIn: false,
    });
    const body = srv.state.lastReq.body.toString();
    expect(body).toContain('name="marketing_opt_in"');
  });

  test('MKT-EC2b marketing_opt_in value is the string "false" when explicitly opted out', async () => {
    const client = makeTestClient(srv.port);
    await client.getForecast({
      csvPath,
      email: 'user@example.com',
      siteName: 'Site',
      location: 'Durban',
      verificationCode: '123456',
      capacityKw: 10.0,
      touAccepted: true,
      marketingOptIn: false,
    });
    const body = srv.state.lastReq.body.toString();
    expect(body).toMatch(/name="marketing_opt_in"[\s\S]*?false/);
  });
});

// ---------------------------------------------------------------------------
// EH-TOU1 — server 400 with ToU-specific error text → ValidationError with
//           that message surfaced
// ---------------------------------------------------------------------------

describe('EH-TOU1 — HTTP 400 ToU rejection surfaces error text in ValidationError', () => {
  let srv;
  let csvPath;

  beforeAll(async () => {
    srv = await startServer((req, res) => {
      res.writeHead(400, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        error: 'You must accept the Terms of Use (tou_accepted=true) to use this service.',
      }));
    });
    csvPath = makeTempCsv();
  });

  afterAll(async () => {
    await srv.close();
    if (fs.existsSync(csvPath)) fs.unlinkSync(csvPath);
  });

  test('EH-TOU1a server ToU 400 rejects with ValidationError', async () => {
    const client = makeTestClient(srv.port);
    await expect(
      client.getForecast({
        csvPath,
        email: 'user@example.com',
        siteName: 'Site',
        location: 'Loc',
        verificationCode: '123456',
        capacityKw: 5.0,
        touAccepted: true,
      })
    ).rejects.toThrow(ValidationError);
  });

  test('EH-TOU1b ValidationError message contains Terms of Use text from server', async () => {
    const client = makeTestClient(srv.port);
    let caught;
    try {
      await client.getForecast({
        csvPath,
        email: 'user@example.com',
        siteName: 'Site',
        location: 'Loc',
        verificationCode: '123456',
        capacityKw: 5.0,
        touAccepted: true,
      });
    } catch (e) {
      caught = e;
    }
    expect(caught).toBeInstanceOf(ValidationError);
    expect(caught.message).toMatch(/Terms of Use/);
  });
});
