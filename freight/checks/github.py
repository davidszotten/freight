from __future__ import absolute_import, unicode_literals

__all__ = ['GitHubContextCheck']

import freight
import requests

from flask import current_app

from freight.exceptions import CheckFailed

from .base import Check


class GitHubContextCheck(Check):
    def get_options(self):
        return {
            'api_root': {'required': False},
            'contexts': {'required': True},
            'repo': {'required': True},
        }

    def check(self, app, sha, config):
        token = current_app.config['GITHUB_TOKEN']
        if not token:
            # TODO(dcramer): error/log this
            return

        api_root = (
            config.get('api_root') or current_app.config['GITHUB_API_ROOT']
        ).rstrip('/')

        contexts = set(config['contexts'])
        repo = config['repo']

        url = '{api_root}/repos/{repo}/commits/{ref}/statuses'.format(
            api_root=api_root,
            repo=repo,
            ref=sha,
        )

        headers = {
            'User-Agent': 'freight/{}'.format(freight.VERSION),
            'Accepts': 'application/json',
            'Authorization': 'token {}'.format(token),
        }

        resp = requests.get(url, headers=headers)

        for data in resp.json():
            if data['context'] not in contexts:
                continue
            if data['state'] != 'success':
                raise CheckFailed('{} context is {}'.format(data['context'], data['state']))
            contexts.remove(data['context'])

        if contexts:
            raise CheckFailed('{} context was not found'.format(iter(contexts).next()))
