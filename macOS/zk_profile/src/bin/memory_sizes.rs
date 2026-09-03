use ark_bls12_381::{Fr, G1Affine, G2Affine};
use std::mem::size_of;

fn main() {
    println!("Fr_memory_bytes={}", size_of::<Fr>());
    println!("G1Affine_memory_bytes={}", size_of::<G1Affine>());
    println!("G2Affine_memory_bytes={}", size_of::<G2Affine>());
}
