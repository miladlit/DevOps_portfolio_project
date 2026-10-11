# Azure infrastructure lab

This defines one Ubuntu 24.04 VM, a 30 GiB Standard HDD OS disk, a static Standard public IPv4 address, a virtual network/subnet, and an SSH-only network security group. App and proxy ports stay on VM loopback and are reached through an SSH tunnel. No cloud resources have been provisioned or billed by this project.

Install Terraform >=1.7 and Azure CLI, authenticate with `az login`, and select your subscription. From `infra/terraform`, supply values through environment variables:

```bash
export TF_VAR_subscription_id='YOUR_SUBSCRIPTION_ID'
export TF_VAR_ssh_public_key="$(cat ~/.ssh/id_ed25519.pub)"
export TF_VAR_admin_cidr='YOUR_PUBLIC_IPV4/32'
terraform fmt -check
terraform init
terraform validate
terraform plan -out=learning.tfplan
```

Inspect every planned resource and verify the selected region, VM SKU availability, access rule, and cost before applying. The default region is Sweden Central and VM SKU is Standard_B1s; change `TF_VAR_vm_size` if your subscription does not offer that SKU. State and saved plans are ignored because they contain infrastructure details. This learning configuration uses local state; retain it securely until teardown. For team use, configure an Azure Storage backend with access controls and state locking.

Applying creates billable resources:

```bash
terraform apply learning.tfplan
terraform output -raw public_ip
```

After creating the VM, follow [Ansible deployment](../../deploy/ansible/README.md). Reach the proxy from your workstation with `ssh -L 9000:127.0.0.1:8080 deploy@YOUR_PUBLIC_IP` and browse http://127.0.0.1:9000. Ansible supplies systemd and Nginx; Terraform only creates infrastructure.

## Cost worksheet and teardown

Use the [Azure pricing calculator](https://azure.microsoft.com/en-us/pricing/calculator/) for your subscription currency and region. Record a dated estimate before apply:

| Resource | Quantity | Estimate input |
| --- | --- | --- |
| Linux Standard_B1s | 1 VM | Hourly compute price × planned running hours (24 for a one-day lab, 730 for a month) |
| Standard HDD OS disk | 1 × 30 GiB | Applicable disk tier monthly price × fraction of month retained |
| Standard static IPv4 | 1 address | Hourly IP price × allocated hours |
| Network transfer | Actual outgoing GB | Regional transfer charge after applicable allowance |

Total = compute + disk + IP + transfer + taxes. No numerical quote is recorded yet; actual SKU availability and prices require an Azure subscription/region check. A stopped VM may still incur disk and IP costs. The 1 GiB VM is for the small app/proxy, not the Elastic monitoring lab. Set a budget alert in Azure and keep the lab short.

When done, review and destroy only this configuration's resources:

```bash
terraform plan -destroy
terraform destroy
az group exists --name service-status-rg
```

The final command should return `false` if the default prefix was used. Keep state until deletion is confirmed. Verify Azure Cost Management for residual resources or charges. Runtime provisioning, cost quote, deployment, and teardown checks remain pending explicit cloud execution.

Reference: [AzureRM Linux VM](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs/resources/linux_virtual_machine).
