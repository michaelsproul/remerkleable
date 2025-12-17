"""
Test case for empty progressive bitlist tree hash root fix.

According to EIP-7916, the merkleization of a progressive bitlist should be:
mix_in_length(merkleize_progressive(pack_bits(value)), len(value))

For an empty bitlist (length 0):
1. Even an empty bitlist has at least one chunk for merkleization (all zeros)
2. merkleize_progressive([zero_chunk]) = hash(0x00*32, 0x00*32) = f5a5fd42...
3. mix_in_length(f5a5fd42..., 0) = hash(f5a5fd42..., 0x00*32) = 7a0501f5...

This test confirms that the fix correctly implements this behavior.

Issue: Empty progressive bitlists were using zero_node(0) instead of having
one zero chunk, resulting in an incorrect tree hash root.

Fix: Modified ProgressiveBitlist.__new__, default_node, and deserialize to
ensure empty bitlists have one zero chunk.
"""

from remerkleable.progressive import ProgressiveBitlist
from hashlib import sha256
import io


def test_empty_progressive_bitlist_tree_hash():
    """Test that empty progressive bitlist has correct tree hash root."""
    pb = ProgressiveBitlist()
    
    # Get tree hash root
    root = pb.get_backing().merkle_root()
    
    # Expected: hash(hash(0x00*32, 0x00*32), 0x00*32)
    # Step 1: merkleize_progressive([zero_chunk])
    merkleize_result = sha256(b'\x00' * 64).digest()
    assert merkleize_result.hex() == 'f5a5fd42d16a20302798ef6ed309979b43003d2320d9f0e8ea9831a92759fb4b'
    
    # Step 2: mix_in_length(merkleize_result, 0)
    expected_root = sha256(merkleize_result + b'\x00' * 32).digest()
    assert expected_root.hex() == '7a0501f5957bdf9cb3a8ff4966f02265f968658b7a9c62642cba1165e86642f5'
    
    # Verify the actual root matches
    assert root.hex() == expected_root.hex()
    
    # Verify serialization is still correct (just the delimiting bit)
    serialized = pb.encode_bytes()
    assert serialized.hex() == '01'
    
    # Verify length is 0
    assert pb.length() == 0


def test_empty_progressive_bitlist_deserialization():
    """Test that deserializing an empty progressive bitlist works correctly."""
    # Deserialize 0x01 (empty bitlist with just the delimiting bit)
    stream = io.BytesIO(bytes.fromhex("01"))
    pb = ProgressiveBitlist.deserialize(stream, 1)
    
    # Verify length
    assert pb.length() == 0
    
    # Verify tree hash root
    root = pb.get_backing().merkle_root()
    assert root.hex() == '7a0501f5957bdf9cb3a8ff4966f02265f968658b7a9c62642cba1165e86642f5'
    
    # Verify round-trip
    serialized = pb.encode_bytes()
    assert serialized.hex() == '01'


def test_empty_progressive_bitlist_default_node():
    """Test that the default node for ProgressiveBitlist is correct."""
    default = ProgressiveBitlist.default_node()
    
    # The default node should have the correct tree hash
    assert default.merkle_root().hex() == '7a0501f5957bdf9cb3a8ff4966f02265f968658b7a9c62642cba1165e86642f5'


def test_non_empty_progressive_bitlist_still_works():
    """Test that non-empty progressive bitlists still work correctly after the fix."""
    # Create a non-empty progressive bitlist
    pb = ProgressiveBitlist(1, 1, 0, 1, 0, 1, 0, 0)  # TTFTFTFF
    
    # Verify length
    assert pb.length() == 8
    
    # Verify serialization
    assert pb.encode_bytes().hex() == '2b01'
    
    # Test round-trip
    stream = io.BytesIO(pb.encode_bytes())
    pb2 = ProgressiveBitlist.deserialize(stream, len(pb.encode_bytes()))
    assert pb2.length() == 8
    assert pb2.encode_bytes() == pb.encode_bytes()
    assert pb2.get_backing().merkle_root() == pb.get_backing().merkle_root()


if __name__ == '__main__':
    test_empty_progressive_bitlist_tree_hash()
    print("✓ Empty progressive bitlist tree hash test passed!")
    
    test_empty_progressive_bitlist_deserialization()
    print("✓ Empty progressive bitlist deserialization test passed!")
    
    test_empty_progressive_bitlist_default_node()
    print("✓ Empty progressive bitlist default node test passed!")
    
    test_non_empty_progressive_bitlist_still_works()
    print("✓ Non-empty progressive bitlist test passed!")
    
    print("\n✅ All tests passed!")
