use ark_bls12_381::{Fr, G1Affine, G2Affine};
use ark_ec::AffineRepr;
use ark_serialize::CanonicalSerialize;
use ark_std::Zero;

fn compressed_size<T: CanonicalSerialize>(x: &T) -> usize {
    x.compressed_size()
}

fn uncompressed_size<T: CanonicalSerialize>(x: &T) -> usize {
    x.uncompressed_size()
}

fn main() {
    let fr = Fr::zero();
    let g1 = G1Affine::zero();
    let g2 = G2Affine::zero();

    println!(
        "Fr,compressed={},uncompressed={}",
        compressed_size(&fr),
        uncompressed_size(&fr)
    );

    println!(
        "G1Affine,compressed={},uncompressed={}",
        compressed_size(&g1),
        uncompressed_size(&g1)
    );

    println!(
        "G2Affine,compressed={},uncompressed={}",
        compressed_size(&g2),
        uncompressed_size(&g2)
    );
}
