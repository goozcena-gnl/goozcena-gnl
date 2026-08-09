# Platform engineering, from foundations to delivery

I build evidence-backed platform engineering projects that connect developer experience, cloud governance, operational automation, infrastructure experimentation, and GitOps delivery. Each repository documents its validation boundary, operational trade-offs, and reproducible evidence.

**Core domains:** Platform Engineering · Kubernetes and GitOps · Infrastructure as Code · DevOps/SRE automation · Kubernetes virtualization

## Engineering journey

1. **Design the platform — [Cloud-Native Internal Developer Platform](https://github.com/goozcena-gnl/cloud-native-idp-platform)**

   A local-first Kubernetes IDP combining Backstage golden paths, Argo CD, SRE telemetry, policy, secrets, cost visibility, and recovery evidence.

2. **Govern the cloud foundation — [Azure Data Landing Zone Platform](https://github.com/goozcena-gnl/azure-data-landing-zone-platform)**

   A Terraform-based Azure landing-zone lab with governance, secure remote state, and a validated deploy–drift-check–destroy foundation lifecycle.

3. **Automate operations — [DevOps Automation Toolkit](https://github.com/goozcena-gnl/devops-automation-toolkit)**

   A read-only-first Python CLI with 20 deterministic DevOps, SRE, and DevSecOps tools producing redacted JSON, Markdown, and SARIF reports; `v1.0.1` is its current stable GitHub Release.

4. **Solve unusual infrastructure problems — [FluxVirt Lab](https://github.com/goozcena-gnl/fluxvirt-lab)**

   A K3s, Flux CD, and KubeVirt lab demonstrating VM/container convergence, nested virtualization, and one checksum-verified isolated VM-disk recovery exercise.

5. **Deliver workloads safely — [Flask Kubernetes GitOps Lab](https://github.com/goozcena-gnl/flask-kubernetes-gitops-lab)**

   A hardened Flask delivery chain validated on Minikube, where GitLab CI publishes immutable OCI images and Argo CD alone reconciles Kubernetes.

## Evidence boundaries

These repositories document scoped engineering projects, not production adoption. Their READMEs distinguish implemented design, static validation, retained lab or runtime evidence, and paths that were not exercised against live target environments.
