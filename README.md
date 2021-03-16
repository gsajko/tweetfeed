# custom-twitter-feed
## 1. Overview

*A summary of the doc's purpose, problem, solution, and desired outcome, usually in 3-5 sentences.*

## 2. Motivation
*Why the problem is important to solve, and why now.*

## 3. Success metrics
*Usually framed as business goals, such as increased customer engagement (e.g., CTR, DAU), revenue, or reduced cost.*

## 4. Requirements & Constraints
*Functional requirements are those that should be met to ship the project. They should be described in terms of the customer perspective and benefit.*


*Non-functional/technical requirements are those that define system quality and how the system should be implemented. These include performance (throughput, latency, error rates), cost (infra cost, ops effort), security, data privacy, etc.*

*Constraints can come in the form of non-functional requirements (e.g., cost below $`x` a month, p99 latency < `y`ms)*

### 4.1 What's in-scope & out-of-scope?
*Some problems are too big to solve all at once. Be clear about what's out of scope.*

## 5. Methodology

### 5.1. Problem statement

*How will you frame the problem? For example, fraud detection can be framed as an unsupervised (outlier detection, graph cluster) or supervised problem (e.g. classification).*

### 5.2. Data

*What data will you use to train your model? What input data is needed during serving?*

### 5.3. Techniques

*What machine learning techniques will you use? How will you clean and prepare the data (e.g., excluding outliers) and create features?*

### 5.4. Experimentation & Validation

*How will you validate your approach offline? What offline evaluation metrics will you use?*

*If you're A/B testing, how will you assign treatment and control (e.g., customer vs. session-based) and what metrics will you measure? What are the success and [guardrail](https://medium.com/airbnb-engineering/designing-experimentation-guardrails-ed6a976ec669) metrics?*

### 5.5. Human-in-the-loop

*How will you incorporate human intevention into your ML system (e.g., product/customer exclusion lists)?*

## 6. Implementation

### 6.1. High-level design

![](https://upload.wikimedia.org/wikipedia/commons/thumb/2/2e/Data-flow-diagram-example.svg/1280px-Data-flow-diagram-example.svg.png)

*Start by providing a big-picture view. [System-context diagrams](https://en.wikipedia.org/wiki/System_context_diagram) and [data-flow diagrams](https://en.wikipedia.org/wiki/Data-flow_diagram) work well.*

### 6.2. Infra

*How will you host your system? On-premise, cloud, or hybrid? This will define the rest of this section*

### 6.3. Performance (Throughput, Latency)

*How will your system meet the throughput and latency requirements? Will it scale vertically or horizontally?*

### 6.4. Security

*How will your system/application authenticate users and incoming requests? If its publicly accessible, will it be behind a firewall?*

### 6.5. Data privacy

*How will you ensure the privacy of customer data? Will your system be compliant with data retention and deletion policies (e.g., [GDPR](https://gdpr.eu/what-is-gdpr/)?*

### 6.6. Monitoring & Alarms

*What metrics will you monitor and how? Will you have alarms if a metric breaches a threshold or something else goes wrong?*

### 6.7. Cost
*How much will it cost to build and operate your system? Share estimated monthly costs (e.g., EC2 instances, Lambda, etc.)*

### 6.8. Integration points

*How will your system integrate with upstream data and downstream users?*

### 6.9. Risks & Uncertainties

*Risks are the unknown unknowns; uncertainies are the unknown unknows. What worries you and you would like others to review?*

## 7. Appendix

### 7.1. Alternatives

*What alternatives did you consider and exclude? List pros and cons of each alternative and the rationale for your decision.*

### 7.2. Experiment Results

*Share any results of offline experiments that you conducted.*

### 7.3. Performance benchmarks

*Share any performance benchmarks you ran (e.g., throughput vs. latency vs. instance size/count).*

### 7.4. Milestones & Timeline

*What are the key milestones for this system and the estimated timeline?*

### 7.5. Glossary

*Define and link to business or technical terms.*

### 7.6. References

*Add references that you might have consulted for your methodology.*



Build on a [template](https://github.com/eugeneyan/ml-design-docs) for design docs for machine learning systems based on this [post](https://eugeneyan.com/writing/ml-design-docs/).