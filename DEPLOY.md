# Deploying Forge to AWS

Single small EC2 box running the production Docker stack, reached through a
Cloudflare tunnel (no domain needed to start). Deploys are **manual** — you click
"Run workflow" in GitHub Actions; it builds ARM64 images, pushes to ECR, and rolls
out on the box via SSM Run Command. **No SSH and no inbound ports are required for
a deploy.**

```
 You click "Run workflow"
        │
        ▼
 GitHub Actions ──build linux/arm64──▶ ECR (forge/forge-backend, forge/forge-web)
   (auth: GitHub OIDC ──▶ forge-github-deploy role, no stored keys)
        │                                      ▲
        └──aws ssm send-command──▶ EC2 box ────┘ (pulls images via instance role)
                                      │
                                 docker compose up -d
                                      │
            cloudflared ──outbound 443──▶ Cloudflare ──HTTPS──▶ you
```

Why this shape: ~50 MB of data and a single user don't justify ECS/RDS/ALB. Revisit
RDS when someone else's data is at stake; ECS+ALB when you want hands-off ops or a
second instance. The whole app is **single-origin** — the `web` image
(`frontend/Dockerfile.prod` → Caddy) serves the built SPA and reverse-proxies
`/api/*` to `backend` (`frontend/Caddyfile`), so it lives on one host/port behind the
tunnel (one hostname over 443). `frontend/src/lib/api.ts`: unset/empty `VITE_API_BASE`
keeps the dev `:8001` default; the prod build passes `"/"` to mean same-origin.

## As-built facts (this deployment)

| Thing | Value |
|---|---|
| Region | `us-east-2` |
| Account | `924399325393` |
| ECR registry (host) | `924399325393.dkr.ecr.us-east-2.amazonaws.com` |
| ECR repos | `forge/forge-backend`, `forge/forge-web` |
| EC2 instance | `i-019f15058f91da840` — `t4g.small`, ARM64, Ubuntu 26.04 (user `ubuntu`) |
| Instance role | `forge-ec2-role` (ECR read + SSM core + read the secret) |
| Secret | Secrets Manager `forge/anthropic-api-key` |
| CI deploy role | `forge-github-deploy` (GitHub OIDC, scoped to this repo) |
| GitHub repo | `yimngli470-netizen/interview-planning` |

---

## A. One-time AWS setup (Console)

All resources are namespaced `forge*` so they don't collide with other projects in
the account.

### 1. ECR repositories
ECR → Create repository → Private → **`forge/forge-backend`**; repeat for
**`forge/forge-web`**. The registry host is `924399325393.dkr.ecr.us-east-2.amazonaws.com`
(the `forge/...` part is the repo name).

### 2. EC2 instance
Ubuntu 26.04 **arm64**, `t4g.small`, 30 GB gp3. (Any ARM/Graviton type works; the
images are built `linux/arm64`. An x86 box would need the workflow switched to
`linux/amd64`.)

### 3. Instance IAM role — `forge-ec2-role`
IAM → Roles → Create role → trusted entity **EC2**. Attach:
- `AmazonSSMManagedInstanceCore` — lets the deploy run commands + Session Manager.
- `AmazonEC2ContainerRegistryReadOnly` — pull images from ECR.

Plus an **inline policy** `forge-read-secret` so the box can read the API key:
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "ForgeReadAnthropicSecret",
    "Effect": "Allow",
    "Action": "secretsmanager:GetSecretValue",
    "Resource": "arn:aws:secretsmanager:us-east-2:924399325393:secret:forge/anthropic-api-key-*"
  }]
}
```
Then **EC2 → Instances → select the instance → Actions → Security → Modify IAM role**
→ attach `forge-ec2-role`. Confirm it shows **Online** in **Systems Manager → Fleet
Manager** (proves agent + role + connectivity — the deploy depends on this).

### 4. Secret — `forge/anthropic-api-key`
Secrets Manager → Store a new secret → **Other type of secret → Plaintext** → paste the
raw `sk-ant-...` key → default `aws/secretsmanager` key → name **`forge/anthropic-api-key`**
→ rotation disabled. The deploy fetches it at rollout via the instance role; it is
**never written to disk**. (Skip this to run without AI auto-fill — the deploy tolerates
a missing secret.)

### 5. GitHub OIDC + deploy role — `forge-github-deploy`
- IAM → Identity providers → Add provider → OpenID Connect →
  URL `https://token.actions.githubusercontent.com`, audience `sts.amazonaws.com`.
  (Account-global; reuse if it already exists. The Console manages the thumbprint.)
- IAM → Roles → Create role → **Web identity** → that provider, audience
  `sts.amazonaws.com`, org `yimngli470-netizen`, repo `interview-planning`. Name
  **`forge-github-deploy`**. Trust policy condition (the security boundary — only this
  repo can assume the role):
  ```
  "token.actions.githubusercontent.com:sub": "repo:yimngli470-netizen/interview-planning:*"
  ```
- Inline policy `forge-deploy-permissions` — ECR push (scoped to the two repos) + SSM
  `SendCommand` to the instance/`AWS-RunShellScript` + read command results. Full JSON
  is in the project chat / git history.

### 6. GitHub repo secrets
Repo → Settings → Secrets and variables → Actions:

| Secret | Value |
|---|---|
| `AWS_REGION` | `us-east-2` |
| `AWS_ROLE_ARN` | `arn:aws:iam::924399325393:role/forge-github-deploy` |
| `ECR_REGISTRY` | `924399325393.dkr.ecr.us-east-2.amazonaws.com` |
| `INSTANCE_ID` | `i-019f15058f91da840` |

---

## B. Box setup (Ubuntu 26.04, ARM64) — over SSH or SSM Session Manager

> Shell access: SSH with your key **or** keyless via **Systems Manager → Session
> Manager**. If the SSH security-group rule is `0.0.0.0/0`, tighten it to your IP
> (EC2 → Security Groups → inbound → SSH source "My IP").

```bash
# Docker + compose plugin (the script handles arm64):
sudo apt-get update
curl -fsSL https://get.docker.com -o /tmp/get-docker.sh
sudo sh /tmp/get-docker.sh
sudo usermod -aG docker ubuntu          # then log out/in so the group applies
docker --version && docker compose version

# git + AWS CLI (arm64) — the deploy logs in to ECR + reads the secret on the box:
sudo apt-get install -y git unzip
curl -sSL "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o /tmp/awscli.zip
cd /tmp && unzip -q awscli.zip && sudo ./aws/install

# SSM agent (Ubuntu ships it via snap) — required for Run Command deploys:
sudo snap services amazon-ssm-agent     # expect: active

# Clone the (public) repo + create the chmod-600 env file (NO secret in it):
sudo mkdir -p /opt/forge && sudo chown ubuntu:ubuntu /opt/forge
git clone https://github.com/yimngli470-netizen/interview-planning.git /opt/forge
cat > /opt/forge/.env <<'EOF'
ECR_REGISTRY=924399325393.dkr.ecr.us-east-2.amazonaws.com
POSTGRES_PASSWORD=change-me-to-something-random
EOF
chmod 600 /opt/forge/.env
```
The `ANTHROPIC_API_KEY` is intentionally **not** in `.env` — the deploy fetches it from
Secrets Manager and `export`s it, which overrides `.env` in compose. Don't bring the
stack up by hand; the first deploy (Section C) does it.

---

## C. Deploying (every time)

1. Push commits to `main` (nothing deploys automatically).
2. GitHub → **Actions → Deploy → Run workflow** (or `gh workflow run deploy`).
   Optional tag input; default is the commit SHA.
3. The run builds ARM64 → pushes to ECR → SSM-runs on the box: `git pull`, ECR
   `docker login`, fetch the secret, `docker compose pull && up -d`, prune. The run log
   shows the box's stdout + final status.

**Get the public URL** (the quick tunnel prints a new ephemeral one each restart):
```bash
cd /opt/forge && docker compose -f docker-compose.deploy.yml logs cloudflared | grep trycloudflare
```

---

## D. Operating

- **Logs:** `docker compose -f docker-compose.deploy.yml logs -f backend|web|cloudflared`
- **Shell:** SSM Session Manager (no open port) or SSH.
- **Backups (recommended):** nightly `pg_dump` → S3 — durability without RDS:
  ```bash
  # crontab -e on the box, 03:00 daily (adjust the db container name from `docker ps`):
  0 3 * * * docker exec forge-db-1 pg_dump -U prep prep | gzip | \
    aws s3 cp - s3://<your-bucket>/forge/$(date +\%F).sql.gz
  ```

---

## E. Upgrade paths

- **Stable URL / custom domain:** add a domain to Cloudflare (free), create a **named
  tunnel**, and swap the `cloudflared` command in `docker-compose.deploy.yml` to
  `tunnel run --token ${CLOUDFLARE_TUNNEL_TOKEN}` (put the token in `/opt/forge/.env`).
- **RDS / ECS / ALB:** only when the triggers hit — another user's data (RDS),
  hands-off ops or a second instance (ECS + ALB).
