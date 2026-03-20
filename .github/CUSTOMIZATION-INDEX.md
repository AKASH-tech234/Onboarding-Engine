# Onboarding-Engine Copilot Customizations

This repository includes custom agents and skills for this chat.

## How to use in chat

### Custom agents

Use an agent directly by mentioning it with @ in chat:

- @onboarding-backend-engineer
- @onboarding-integration-debugger
- @onboarding-catalog-curator
- @onboarding-frontend-scaffolder
- @onboarding-plan-maintainer

Example:

- @onboarding-backend-engineer add validation for missing jd_text in analyze route

### Skills

Skills are available for automatic use when your request matches their description. You can also explicitly request them.

Available skills:

- algorithmic-art
- web-artifacts-builder

Example explicit requests:

- Use the algorithmic-art skill to generate a p5.js concept and artifact
- Use the web-artifacts-builder skill to scaffold a React artifact and bundle it

Tip:

- In chat, type / and check suggestions. If a skill is listed as a slash command, invoke it there directly.

## Agent quick guide

- onboarding-backend-engineer:
  Best for Express route/controller/middleware/service implementation in Backend/src.

- onboarding-integration-debugger:
  Best for tracing and fixing end-to-end flow from upload to ML service response.

- onboarding-catalog-curator:
  Best for course catalog/sample result schema alignment and catalog API impact.

- onboarding-frontend-scaffolder:
  Best for Frontend API wiring, upload/result views, and UX states.

- onboarding-plan-maintainer:
  Best for maintaining flow.md, PLAN-1.md, and delivery milestones.
