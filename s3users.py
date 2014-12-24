#!/usr/bin/env python2
import uuid
import argparse
from keystoneclient.v2_0 import client


def rand():
    return str(uuid.uuid4()).replace('-', '')


def get_first_of_name(lst, name):
    '''A bit crazy, return the first item where
    item.name matches given name,returns none otherwise'''
    return next((it for it in lst if it.name == name), None)


def get_or_create_tenant(keystone, tenant_name):
    return (get_first_of_name(keystone.tenants.list(), tenant_name)
            or keystone.tenants.create(tenant_name))


def get_role_id(keystone, role_name):
    return (get_first_of_name(keystone.roles.list(), role_name)
            or keystone.roles.create(role_name))


def add_tenant_role(user, role_name, tenant):
    return (get_first_of_name(keystone.roles.roles_for_user(user, tenant),
                              role_name)
            or keystone.add_user_role(user, get_role_id(keystone, "_member_"),
                                      tenant))


def get_or_create_user(keystone, tenant, user_name=rand()):
    user = get_first_of_name(keystone.users.list(), user_name)
    if user is None:
        user = keystone.users.create(user_name, password="nova",
                                     email=user_name+"@example.com")
    add_tenant_role(user, "Member", tenant)
    return user


def create_ec2_credentials(keystone, user, tenant):
    lst = keystone.ec2.list(user.id)
    if lst:
        return lst[0].access, lst[0].secret
    else:
        keys = keystone.ec2.create(user.id, tenant.id)
        return keys.access, keys.secret


# Major hack. we'll use format for now...
def create_conf_file(keystone, host, port, outfile):
    main_tenant = get_or_create_tenant(keystone, "s3tenant1")
    main_user = get_or_create_user(keystone, main_tenant, "s3user1")
    main_akey, main_skey = create_ec2_credentials(keystone,
                                                  main_user, main_tenant)
    alt_tenant = get_or_create_tenant(keystone, "s3tenant2")
    alt_user = get_or_create_user(keystone, alt_tenant, "s3user2")
    alt_akey, alt_skey = create_ec2_credentials(keystone, alt_user, alt_tenant)
    conf = '''
[DEFAULT]
host = {host}
port = {port}
is_secure = no

[fixtures]
bucket prefix = s3tests-{{random}}

[s3 main]
user_id = {user_id_main}
display_name = {user_name_main}
access_key = {akey_main}
secret_key = {skey_main}
email = {email_main}

[s3 alt]
user_id = {user_id_alt}
display_name = {user_name_alt}
email = {email_alt}
access_key = {akey_alt}
secret_key = {skey_alt}
'''.format(host=host, port=port, random="random",
           user_id_main=main_tenant.id, user_name_main=main_tenant.name,
           user_id_alt=alt_tenant.id, user_name_alt=alt_tenant.name,
           skey_main=main_skey, akey_main=main_akey,
           akey_alt=alt_akey, skey_alt=alt_skey,
           email_main=main_user.email, email_alt=alt_user.email)

    with open(outfile, 'wt') as f:
        f.write(conf)

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description="Create some s3 users and other things")
    parser.add_argument('--token', type=str, default='nova',
                        help='keystone admin token')
    parser.add_argument('--endpoint', type=str,
                        default='http://127.0.0.1:35357/v2.0',
                        help='keystone admin endpoint')
    parser.add_argument('--s3host', type=str,
                        default='127.0.0.1',
                        help='S3 hostname to use')
    parser.add_argument('--port', type=str, default='80',
                        help='S3 Port to use')
    parser.add_argument('-o', type=str, default='s3.conf',
                        help='Output filename')

    args = parser.parse_args()

    keystone = client.Client(token=args.token, endpoint=args.endpoint)

    create_conf_file(keystone, args.s3host, args.port, args.o)
