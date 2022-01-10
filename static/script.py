from kiteconnect import KiteConnect

kite = KiteConnect(api_key="5ov2hsy5honz4378")

# print(kite.login_url())

data = kite.generate_session("LSK3T6ppWqgLhfe47ESzyJyRRNAPJWP8", api_secret="44431oahmqfznkrnw9tu25bdahgvt4c2")
kite.set_access_token(data["access_token"])