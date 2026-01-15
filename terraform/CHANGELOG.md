# 📝 Changelog - Terraform

## Mudanças para Analytics Only

### ✅ O que foi feito:

1. **Variáveis de controle adicionadas**:
   - `enable_rds` (default: `false`) - Controla criação do RDS
   - `enable_vpc` (default: `false`) - Controla criação da VPC

2. **Recursos tornados condicionais**:
   - `rds.tf`: Todos os recursos RDS agora são criados apenas se `enable_rds = true`
   - `network.tf`: Todos os recursos de rede agora são criados apenas se `enable_vpc = true`
   - `outputs.tf`: Outputs do RDS e VPC retornam `null` se desabilitados

3. **Documentação**:
   - `README.md`: Guia completo de uso
   - `terraform.tfvars.example`: Atualizado com novas variáveis

### 🎯 Para Analytics (Recomendado):

```hcl
# terraform.tfvars
enable_rds = false
enable_vpc = false
```

**Recursos criados:**
- ✅ S3 Bucket (Data Lake)
- ✅ S3 Bucket (Athena Results)
- ✅ Glue Database
- ✅ Glue Crawlers (Sport + Financial)
- ✅ Athena Workgroup

**Recursos NÃO criados:**
- ❌ RDS PostgreSQL
- ❌ VPC/Network

### ⚠️ Importante:

- **RDS requer VPC**: Se `enable_rds = true`, também precisa `enable_vpc = true`
- **S3/Glue/Athena não precisam de VPC**: Funcionam sem rede dedicada
- **Custo reduzido**: Sem RDS = sem custo fixo mensal

### 🔄 Como Remover Recursos Existentes:

Se você já tem RDS/VPC criados e quer remover:

1. Edite `terraform.tfvars`:
   ```hcl
   enable_rds = false
   enable_vpc = false
   ```

2. Execute:
   ```bash
   terraform plan   # Ver o que será destruído
   terraform apply  # Aplicar mudanças (destruirá RDS e VPC)
   ```

### 📊 Comparação de Custos:

**Antes (com RDS):**
- RDS db.t3.micro: ~$15/mês
- VPC: Gratuito
- S3: ~$0.023/GB/mês
- Glue: ~$0.44/crawler-run
- Athena: ~$5/TB escaneado

**Depois (sem RDS):**
- S3: ~$0.023/GB/mês
- Glue: ~$0.44/crawler-run
- Athena: ~$5/TB escaneado
- **Economia: ~$15/mês** (sem custo fixo do RDS)
