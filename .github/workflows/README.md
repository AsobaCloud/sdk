# GitHub Actions CI/CD Pipeline

This directory contains GitHub Actions workflows for the Ona SDK project's CI/CD pipeline.

## Overview

The CI/CD pipeline provides automated linting, testing, and regression testing for both Python and JavaScript components, ensuring code quality and preventing regressions across the multi-language SDK.

## Workflow Structure

### Core Workflows

1. **Python CI/CD** (`python-ci.yml`) - Python-specific linting, testing, and dependency validation
2. **JavaScript CI/CD** (`javascript-ci.yml`) - JavaScript-specific linting, testing, and dependency validation
3. **Integration Testing** (`integration-ci.yml`) - Cross-language integration and API compatibility tests
4. **Security Scanning** (`security-ci.yml`) - Security scanning and vulnerability detection
5. **Performance Monitoring** (`performance-ci.yml`) - Performance benchmarking and monitoring (scheduled)
6. **Documentation Validation** (`docs-ci.yml`) - Documentation validation and example verification
7. **Pull Request Validation** (`pr-validation.yml`) - Pull request validation and status checks

### Support Files

1. **Common Configuration** (`_common.yml`) - Shared configuration reused across workflows
2. **Workflow Template** (`_template.yml`) - Template for creating new workflows
3. **Permissions Configuration** (`../permissions.yml`) - GitHub Actions permissions settings

## Configuration

### Environment Variables

Common environment variables are defined in `_common.yml`:

- `PYTHON_VERSION`: Default Python version (3.11)
- `NODE_VERSION`: Default Node.js version (20)
- `REPO_NAME`: Repository name
- `BRANCH_NAME`: Current branch name
- `CACHE_PREFIX`: Cache key prefix
- `ARTIFACT_RETENTION_DAYS`: Artifact retention period (7 days)

### Permissions

Permissions are configured in `../permissions.yml`:

- Default permissions for all workflows
- Workflow-specific permissions
- Environment-specific permissions
- Branch protection rules
- Secret management

### Cache Configuration

Caching is configured to improve workflow performance:

- Python: pip cache and virtual environments
- JavaScript: node_modules and npm cache
- General: Temporary files and build artifacts

## Usage

### Triggering Workflows

Workflows are automatically triggered on:

- **Push**: Code pushes to any branch
- **Pull Request**: PR opens or updates
- **Schedule**: Scheduled execution (for performance monitoring)
- **Manual**: Manual trigger via `workflow_dispatch`

### Manual Execution

To manually trigger a workflow:

1. Go to the "Actions" tab in GitHub
2. Select the workflow you want to run
3. Click "Run workflow"
4. Select the branch and provide any required inputs

### Viewing Results

Workflow results can be viewed:

1. **GitHub Actions UI**: Detailed logs and job status
2. **Artifacts**: Test reports, coverage data, and other outputs
3. **Status Checks**: PR status checks and merge blocking
4. **Notifications**: Failure notifications and summary reports

## Development

### Creating New Workflows

Use the template file (`_template.yml`) as a starting point:

```yaml
# Copy the template
cp .github/workflows/_template.yml .github/workflows/new-workflow.yml

# Customize the workflow
# 1. Update the workflow name
# 2. Customize triggers if needed
# 3. Implement job logic
# 4. Add workflow-specific configuration
```

### Testing Workflows

To test workflow changes:

1. **Local Validation**: Use `act` for local testing (if installed)
2. **Branch Testing**: Push to a feature branch and monitor execution
3. **Dry Runs**: Use `workflow_dispatch` for manual testing

### Best Practices

1. **Reuse Configuration**: Use common configuration from `_common.yml`
2. **Matrix Builds**: Test multiple versions of Python/Node.js
3. **Caching**: Cache dependencies to improve performance
4. **Artifacts**: Upload test reports and coverage data
5. **Notifications**: Configure appropriate notification channels
6. **Cleanup**: Clean up temporary files and resources

## Troubleshooting

### Common Issues

1. **Workflow Not Triggering**
   - Check path filters in workflow triggers
   - Verify branch patterns
   - Check GitHub Actions permissions

2. **Cache Not Restoring**
   - Verify cache key configuration
   - Check cache paths exist
   - Clear cache if corrupted

3. **Permission Errors**
   - Check workflow permissions
   - Verify repository secrets
   - Check branch protection rules

4. **Timeout Issues**
   - Increase job timeout limits
   - Optimize long-running tasks
   - Use parallel execution where possible

### Debugging

1. **Enable Debug Logging**: Add `ACTIONS_STEP_DEBUG: true` to workflow secrets
2. **Check Job Logs**: Review detailed logs in GitHub Actions UI
3. **Artifact Inspection**: Download and inspect workflow artifacts
4. **Local Reproduction**: Reproduce issues locally when possible

### Getting Help

1. **Documentation**: Check this README and workflow comments
2. **GitHub Actions Docs**: [Official documentation](https://docs.github.com/en/actions)
3. **Community**: GitHub Discussions or community forums
4. **Support**: Contact repository maintainers

## Maintenance

### Regular Tasks

1. **Update Dependencies**: Keep actions and tools up to date
2. **Clean Cache**: Monitor and clean cache usage
3. **Review Logs**: Regularly review workflow logs for issues
4. **Optimize Performance**: Identify and optimize slow jobs

### Monitoring

1. **Success Rates**: Monitor workflow success rates
2. **Execution Times**: Track job execution times
3. **Resource Usage**: Monitor cache and artifact storage
4. **Failure Patterns**: Identify and address recurring failures

### Security

1. **Secret Management**: Regularly rotate secrets
2. **Dependency Scanning**: Monitor for vulnerable dependencies
3. **Permission Review**: Regularly review and update permissions
4. **Audit Logs**: Review GitHub Actions audit logs

## Contributing

When contributing to the CI/CD pipeline:

1. **Follow Templates**: Use existing templates for new workflows
2. **Add Documentation**: Document new workflows and changes
3. **Test Changes**: Test workflow changes before merging
4. **Update README**: Update this documentation as needed

## License

This CI/CD pipeline configuration is part of the Ona SDK project and is subject to the same license terms.