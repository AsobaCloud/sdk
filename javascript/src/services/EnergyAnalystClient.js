/**
 * Energy Analyst RAG Client
 * Provides retrieval-augmented generation for energy policy and regulatory analysis
 */

const { validateRequired, validateString, validateRange } = require('../utils/validators');

/**
 * Client for Energy Analyst RAG Service
 */
class EnergyAnalystClient {
  /**
   * Create a new EnergyAnalystClient
   * @param {HTTPClient} httpClient - HTTP client instance
   * @param {Config} config - SDK configuration
   */
  constructor(httpClient, config) {
    this.client = httpClient;
    this.config = config;
    this.endpoint = config.getEndpoint('energyAnalyst');
  }

  /**
   * Query the RAG system with a question
   * @param {Object} params - Query parameters
   * @param {string} params.question - Question to answer
   * @param {number} [params.n_results=3] - Number of context documents to retrieve (1-10)
   * @param {number} [params.max_new_tokens] - Maximum tokens to generate (50-2048)
   * @param {number} [params.temperature] - Sampling temperature (0.0-2.0)
   * @returns {Promise<Object>} Answer with sources and citation
   */
  async query({ question, n_results = 3, max_new_tokens, temperature }) {
    validateRequired({ question }, ['question']);
    validateString(question, 'question');

    if (n_results !== undefined) {
      validateRange(n_results, 'n_results', 1, 10);
    }

    if (max_new_tokens !== undefined) {
      validateRange(max_new_tokens, 'max_new_tokens', 50, 2048);
    }

    if (temperature !== undefined) {
      validateRange(temperature, 'temperature', 0.0, 2.0);
    }

    const requestBody = { question, n_results };

    if (max_new_tokens !== undefined) {
      requestBody.max_new_tokens = max_new_tokens;
    }

    if (temperature !== undefined) {
      requestBody.temperature = temperature;
    }

    return this.client.post(`${this.endpoint}/query`, requestBody);
  }

  /**
   * Add documents to the vector database
   * @param {Object} params - Document parameters
   * @param {Array<string>} params.texts - List of document texts to add
   * @param {Array<Object>} [params.metadatas] - Optional metadata for each document
   * @returns {Promise<Object>} Status and count of added documents
   */
  async addDocuments({ texts, metadatas }) {
    validateRequired({ texts }, ['texts']);

    if (!Array.isArray(texts) || texts.length === 0) {
      throw new Error('texts must be a non-empty array');
    }

    const requestBody = { texts };

    if (metadatas !== undefined) {
      if (!Array.isArray(metadatas)) {
        throw new Error('metadatas must be an array');
      }
      requestBody.metadatas = metadatas;
    }

    return this.client.post(`${this.endpoint}/add_documents`, requestBody);
  }

  /**
   * Upload PDF files for processing
   * @param {Array<File>} files - PDF files to upload
   * @returns {Promise<Object>} Upload results
   */
  async uploadPDFs(files) {
    if (!Array.isArray(files) || files.length === 0) {
      throw new Error('files must be a non-empty array');
    }

    const formData = new FormData();
    for (const file of files) {
      formData.append('files', file);
    }

    return this.client.post(`${this.endpoint}/upload_pdfs`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  }

  /**
   * Get collection information
   * @returns {Promise<Object>} Collection info
   */
  async getCollectionInfo() {
    return this.client.get(`${this.endpoint}/collection/info`);
  }

  /**
   * Clear all documents from the collection
   * @returns {Promise<Object>} Status message
   */
  async clearCollection() {
    return this.client.delete(`${this.endpoint}/collection/clear`);
  }

  /**
   * Get service health status
   * @returns {Promise<Object>} Health status
   */
  async getHealth() {
    return this.client.get(`${this.endpoint}/health`);
  }
}

module.exports = EnergyAnalystClient;
