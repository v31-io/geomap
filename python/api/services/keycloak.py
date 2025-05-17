import os
import jwt
import requests
from fastapi import HTTPException, Header
from keycloak import KeycloakOpenID


client_id = os.environ["KEYCLOAK_CLIENT_ID"]
keycloak_openid = KeycloakOpenID(
    server_url=f'{os.environ["KEYCLOAK_URL"]}/auth/',
    realm_name='default',
    client_id=client_id
)

jwks_url = f"{os.environ['KEYCLOAK_URL']}/realms/default/protocol/openid-connect/certs"
jwks = requests.get(jwks_url).json()

class TokenVerifier:
  def __init__(self, roles: list = []):
      self.roles = roles

  def __call__(self, authorization: str = Header(None)):
    if not authorization:
      raise HTTPException(status_code=401, detail="Authorization header missing")

    try:
      token = authorization.split(" ")[1]
      header = jwt.get_unverified_header(token)
      key = None
      for k in jwks["keys"]:
        if k["kid"] == header["kid"]:
          key = k
          break
      if not key:
        raise HTTPException(status_code=401, detail="Invalid token")
          
      public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
      decoded_token = jwt.decode(token, public_key, algorithms=[header['alg']],
                                 options={"verify_aud": False})

      # Verify roles
      for role in self.roles:
        if role not in decoded_token['resource_access'][client_id]['roles']:
          raise HTTPException(status_code=401, detail=f'Role [{role}] is required.')
      
      return decoded_token
    
    except jwt.ExpiredSignatureError:
      raise HTTPException(status_code=401, detail="Token expired")
    
    except jwt.InvalidTokenError:
      raise HTTPException(status_code=401, detail="Invalid token")