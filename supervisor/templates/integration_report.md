# Integration Report - {{date}}

## 📊 Summary

- **Branches Merged**: {{merged_count}}/{{total_agents}}
- **Integration Tests**: {{test_pass_rate}}% passing
- **Active Conflicts**: {{conflict_count}}
- **Blockers**: {{blocker_count}}

## 🔀 Merge Velocity

{{#each agents}}
- **{{name}}**: {{status}} ({{merge_date}})
  - Priority: {{priority}}
  - Commits: {{commits_ahead}}
  - Status: {{merge_status}}
{{/each}}

## ⚠️ Issues

{{#if issues}}
{{#each issues}}
### {{title}} [{{status}}]

**Branch**: {{branch}}
**Type**: {{issue_type}}
**Created**: {{created_at}}

{{description}}

**Resolution**: {{resolution}}

---
{{/each}}
{{else}}
✅ No active issues
{{/if}}

## 📅 Next 24h Priority

{{#each priorities}}
{{position}}. {{task}} ({{agent}})
   - **Reason**: {{reason}}
   - **ETA**: {{eta}}
{{/each}}

## 📈 Metrics

### Integration Performance
- **Test Pass Rate**: {{test_pass_rate}}%
- **Mean Time to Merge**: {{mean_time_to_merge}} hours
- **Mean Conflict Resolution Time**: {{mean_conflict_resolution_time}} hours
- **Auto-Resolution Rate**: {{auto_resolution_rate}}%

### Quality Gates
- **Code Quality Score**: {{code_quality_score}}/10
- **Security Issues**: {{security_issues}}
- **Failed Checks**: {{failed_checks}}

### System Health
- **Docker Services**: {{docker_services_running}}/{{docker_services_total}} running
- **GPU Memory**: {{gpu_memory_percent}}%
- **Disk Usage**: {{disk_usage_percent}}%
- **Uptime**: {{system_uptime}} hours

## 🔄 Recent Activity

{{#each recent_activity}}
- **{{timestamp}}**: {{event}} - {{description}}
{{/each}}

## 📝 Notes

{{notes}}

---

**Report Generated**: {{timestamp}}
**Supervisor Version**: 1.0.0
