import uuid 
import argparse
from keystoneclient.v2_0 import client


def get_tenant(keystone, tenant_name):
    tenant = filter(lambda x: x.name == tenant_name,
                    keystone.tenants.list())
    if not tenant:
        return keystone.tenants.create(tenant)
    else:
        return tenant[0]


def create_user(keystone, user_name, tenant):
    
    return keystone.users.create(user_name, password="nova",
                                 email=user_name+"@example.com")
    

def create_conf_file():
    pass

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(
        description="Create some s3 users and other things")
    parser.add_argument('--token', type=str, default='nova',
                        help='keystone admin token')
    parser.add_argument('--endpoint', type=str,
                        default='http://127.0.0.1:35357/v2.0',
                        help='keystone admin endpoint')
    args = parser.parse_args()

    keystone = client.Client(token=args.token, endpoint=args.endpoint)

    

        
