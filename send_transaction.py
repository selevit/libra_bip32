import hashlib

import libra
from canoser import bytes_to_int_list
from libra.transaction.script import Script

from vendor import bip32_ed25519, ed25519

seed = bip32_ed25519.generate_proper_master_secret()
master_private_key, master_public_key, chain_code = bip32_ed25519.root_key(seed)


def child_pubkey(n):
    child, child_chain_code = bip32_ed25519.safe_public_child_key(master_public_key, chain_code, n, False)
    return child


def child_privkey(n):
    child_private, child_public, child_chain_code = bip32_ed25519.private_child_key(
        (master_private_key, master_public_key, chain_code),
        n,
    )
    return child_private


def gen_libra_address(n):
    return hashlib.sha3_256(child_pubkey(n)).hexdigest()


sender_address = gen_libra_address(0)
receiver_address = gen_libra_address(1)

client = libra.Client("testnet")
client.mint_coins_with_faucet_service(receiver=sender_address, micro_libra=1000000,
                                      is_blocking=True)

tx_script = Script.gen_transfer_script(receiver_address, micro_libra=5000)
raw_tx = libra.RawTransaction.new_script_tx(
    sender_address=sender_address,
    sequence_number=client.get_sequence_number(sender_address),
    script=tx_script,
)
tx_hash = raw_tx.hash()

sender_privkey = child_privkey(0)
signature = bip32_ed25519.special_signing(
    kL=sender_privkey[0],
    kR=sender_privkey[1],
    A=child_pubkey(0),
    M=tx_hash,
)
assert ed25519.verify(child_pubkey(0), signature, tx_hash)

signed_txn = libra.SignedTransaction(
    raw_tx,
    bytes_to_int_list(child_pubkey(0)),
    bytes_to_int_list(signature),
)
request = libra.client.SubmitTransactionRequest()
request.signed_txn.signed_txn = signed_txn.serialize()

client.submit_transaction(request, raw_tx, is_blocking=True)

print('Transaction info in libexplorer (should be available in few seconds)')
print(f'Sender transactions: https://libexplorer.com/address/{sender_address}')
print(f'Receiver transactions: https://libexplorer.com/address/{receiver_address}')
