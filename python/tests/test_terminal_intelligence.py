import pytest
from unittest.mock import MagicMock, patch
import json
from ona_platform.services.terminal import TerminalClient

def test_get_site_summary_parsing():
    """Test that get_site_summary correctly parses the expanded response from terminalApi."""
    # Create a client instance with a mock config to avoid real AWS calls
    mock_config = MagicMock()
    mock_config.aws_region = 'af-south-1'
    
    # We mock BaseServiceClient's invoke_lambda method
    with patch('ona_platform.services.terminal.BaseServiceClient.invoke_lambda') as mock_invoke:
        mock_response = {
            'success': True,
            'site_id': 'test-site',
            'summary': {
                'total_kWh_today': 1250.5,
                'fleet_availability_pct': 98.5,
                'fleet_pr_pct': 82.1,
                'battery': {
                    'avg_soh': 94.5,
                    'warranty_status': 'in_warranty',
                    'throughput_kwh': 5000.0,
                    'avg_soc': 80.0,
                    'min_soh': 90.0,
                    'max_soh': 98.0,
                    'total_capacity_kwh': 100.0,
                    'warranty_remaining_pct': 90.0,
                    'cycle_count_estimate': 50.0,
                    'dod_avg': 10.0,
                    'asset_count': 1
                },
                'soiling': {
                    'soiling_rate_pct_day': 0.15,
                    'detected_cleaning_events': [
                        {'timestamp': '2026-05-20T08:00:00Z', 'jump_pct': 5.2, 'pr_before': 0.75, 'pr_after': 0.802}
                    ],
                    'recovery_gain_kwh_last_event': 125.5
                },
                'prognostics': {
                    'battery_rul_days': 1200,
                    'battery_retirement_date': '2029-09-15',
                    'pv_annual_degradation_pct': 0.65,
                    'health_score': 92.4
                },
                'active_inverters': 5,
                'total_inverters': 5,
                'last_updated': '2026-05-31T12:00:00Z'
            }
        }
        mock_invoke.return_value = mock_response
        
        terminal = TerminalClient(mock_config)
        summary = terminal.get_site_summary("test-site")
        
        # Assertions for core fields
        assert summary['total_kWh_today'] == 1250.5
        assert summary['fleet_pr_pct'] == 82.1
        
        # Assertions for new intelligence fields
        assert 'soiling' in summary
        assert summary['soiling']['soiling_rate_pct_day'] == 0.15
        assert len(summary['soiling']['detected_cleaning_events']) == 1
        assert summary['soiling']['recovery_gain_kwh_last_event'] == 125.5
        
        assert 'prognostics' in summary
        assert summary['prognostics']['battery_rul_days'] == 1200
        assert summary['prognostics']['health_score'] == 92.4
        
        assert summary['battery']['avg_soh'] == 94.5

def test_get_site_summary_backward_compatibility():
    """Test that get_site_summary handles responses missing the new fields (old backend version)."""
    mock_config = MagicMock()
    mock_config.aws_region = 'af-south-1'
    
    with patch('ona_platform.services.terminal.BaseServiceClient.invoke_lambda') as mock_invoke:
        mock_response = {
            'success': True,
            'site_id': 'test-site',
            'summary': {
                'total_kWh_today': 1250.5,
                'fleet_availability_pct': 98.5,
                'fleet_pr_pct': 82.1,
                'active_inverters': 5,
                'total_inverters': 5,
                'last_updated': '2026-05-31T12:00:00Z'
                # Missing battery, soiling, prognostics
            }
        }
        mock_invoke.return_value = mock_response
        
        terminal = TerminalClient(mock_config)
        summary = terminal.get_site_summary("test-site")
        
        assert summary['total_kWh_today'] == 1250.5
        assert 'soiling' not in summary
        assert 'prognostics' not in summary
        assert 'battery' not in summary
