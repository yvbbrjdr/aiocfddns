#!/usr/bin/env python3

"""
BSD 3-Clause License

Copyright (c) 2024, yvbbrjdr

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import argparse
import asyncio
import os

import aiostun
import cloudflare

async def get_public_ip(stun_host, stun_port):
    async with aiostun.Client(host=stun_host, port=stun_port) as stunc:
        mapped_addr = await stunc.get_mapped_address()
    if mapped_addr['family'] != 'IPv4':
        raise RuntimeError('STUN server returned non-IPv4 address')
    return mapped_addr['ip']

async def get_cloudflare_zone_id(cloudflare_client, domain):
    zone_name = '.'.join(domain.split('.')[-2:])
    zones = await cloudflare_client.zones.list(name=zone_name)
    if len(zones.result) == 0:
        raise RuntimeError(f'Zone for {zone_name} not found')
    return zones.result[0].id

async def get_cloudflare_dns_record_id(cloudflare_client, zone_id, domain):
    records = await cloudflare_client.dns.records.list(zone_id=zone_id, name=domain, type='A')
    if len(records.result) == 0:
        return
    return records.result[0].id

async def create_cloudflare_dns_record(cloudflare_client, zone_id, domain, content):
    await cloudflare_client.dns.records.create(zone_id=zone_id, name=domain, content=content, type='A')

async def get_cloudflare_dns_record_content(cloudflare_client, zone_id, dns_record_id):
    record = await cloudflare_client.dns.records.get(zone_id=zone_id, dns_record_id=dns_record_id)
    return record.content

async def update_cloudflare_dns_record_content(cloudflare_client, zone_id, dns_record_id, domain, content):
    await cloudflare_client.dns.records.update(zone_id=zone_id, dns_record_id=dns_record_id, name=domain, content=content, type='A')

async def main(args):
    if args.cloudflare_api_token is None:
        raise RuntimeError('Cloudflare API token is not set')

    print(f'Getting public IP from stun:{args.stun_host}:{args.stun_port}...', end='', flush=True)
    public_ip = await get_public_ip(args.stun_host, args.stun_port)
    print(public_ip)

    cloudflare_client = cloudflare.AsyncCloudflare(api_token=args.cloudflare_api_token)
    print(f'Getting Zone ID for {args.domain}...', end='', flush=True)
    zone_id = await get_cloudflare_zone_id(cloudflare_client, args.domain)
    print(zone_id)

    print(f'Getting DNS A record ID for {args.domain}...', end='', flush=True)
    dns_record_id = await get_cloudflare_dns_record_id(cloudflare_client, zone_id, args.domain)
    if dns_record_id is None:
        print(f'Failed!\nDNS A record not found, creating...', end='', flush=True)
        await create_cloudflare_dns_record(cloudflare_client, zone_id, args.domain, public_ip)
        print('Done!')
        return
    print(dns_record_id)

    print(f'Getting DNS A record content for {args.domain}...', end='', flush=True)
    dns_record_content = await get_cloudflare_dns_record_content(cloudflare_client, zone_id, dns_record_id)
    print(dns_record_content)

    if dns_record_content == public_ip:
        print('DNS A record is already up to date')
        return

    print(f'Updating DNS A record for {args.domain}...', end='', flush=True)
    await update_cloudflare_dns_record_content(cloudflare_client, zone_id, dns_record_id, args.domain, public_ip)
    print('Done!')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Update Cloudflare DNS records with your public IP')
    parser.add_argument('-sh', '--stun-host', type=str, default='stun.cloudflare.com', help='The STUN server to use')
    parser.add_argument('-sp', '--stun-port', type=int, default=3478, help='The STUN server port to use')
    parser.add_argument('-cfat', '--cloudflare-api-token', type=str, default=os.getenv('CF_API_TOKEN'), help='The Cloudflare API token to use')
    parser.add_argument('domain', type=str, help='The domain to update')
    args = parser.parse_args()

    try:
        asyncio.run(main(args))
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print(f'Error: {e}')
        exit(1)
