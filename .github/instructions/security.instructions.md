---
name: Security-sensitive code
description: Additional review guidance for likely sensitive paths; semantics still determine audit scope.
applyTo: '**/*auth*/**,**/*auth*.*,**/*session*/**,**/*session*.*,**/*middleware*/**,**/*middleware*.*,**/*security*/**,**/*security*.*,**/api/**,**/routes/**,**/config/**'
---

Read [the security checklist](../../agent-system/workflows/security-checklist.md).
Use the sensitive delivery route for security-relevant changes. These starter
patterns are hints, not complete detection or access controls; adapt them to a real
project and review sensitive behavior even when its filename does not match.