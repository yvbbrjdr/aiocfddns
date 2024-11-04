# aiocfddns

Update Cloudflare DNS records with your public IP.

## Installation

Install the required dependencies:

```bash
pip3 install -r requirements.txt
```

## Running the Script

You can run the script in two ways:

1. Directly with the API token as an argument:

```bash
./aiocfddns.py -cfat <CLOUDFLARE_API_TOKEN> <DOMAIN>
```

2. Using an environment variable:

```bash
export CF_API_TOKEN=<CLOUDFLARE_API_TOKEN>
./aiocfddns.py <DOMAIN>
```

Replace `<CLOUDFLARE_API_TOKEN>` with your actual Cloudflare API token and `<DOMAIN>` with your target domain name.

## Configuration

By default, the script uses:

- STUN server: `stun.cloudflare.com`
- STUN port: `3478`

You can override these defaults using the following options:

- `-sh`: Specify a custom STUN server hostname
- `-sp`: Specify a custom STUN server port

## Behavior

- The script performs a single DNS record update per execution
- To keep your DNS records continuously updated, configure a cron job to run the script periodically
- If no matching DNS record exists, a new A record will be created automatically
- DNS records are updated only when the IP address changes from the current value
- Currently supports IPv4 addresses only
- DNS records are created or updated with a TTL (Time To Live) of 1 minute
