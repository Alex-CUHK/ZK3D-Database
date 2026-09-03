use ark_bls12_381::{Bls12_381, Fr};
use ark_ff::UniformRand;
use ark_groth16::Groth16;
use ark_relations::{
    lc,
    r1cs::{
        ConstraintSynthesizer,
        ConstraintSystemRef,
        SynthesisError,
    },
};
use ark_snark::SNARK;
use ark_std::rand::{rngs::StdRng, SeedableRng};
use std::time::Instant;

#[derive(Clone)]
struct RepeatedSquareCircuit {
    x: Option<Fr>,
    steps: usize,
}

impl ConstraintSynthesizer<Fr> for RepeatedSquareCircuit {
    fn generate_constraints(
        self,
        cs: ConstraintSystemRef<Fr>,
    ) -> Result<(), SynthesisError> {
        let mut value = self.x.unwrap();
        let mut var = cs.new_witness_variable(|| Ok(value))?;

        for _ in 0..self.steps {
            value *= value;

            let next = cs.new_witness_variable(|| Ok(value))?;

            cs.enforce_constraint(
                lc!() + var,
                lc!() + var,
                lc!() + next,
            )?;

            var = next;
        }

        Ok(())
    }
}

fn run_case(steps: usize, run_id: usize) {
    let seed = 20260827u64 + run_id as u64;
    let mut rng = StdRng::seed_from_u64(seed);

    let x = Fr::rand(&mut rng);

    let setup_circuit = RepeatedSquareCircuit {
        x: Some(x),
        steps,
    };

    let prove_circuit = RepeatedSquareCircuit {
        x: Some(x),
        steps,
    };

    let setup_start = Instant::now();

    let (pk, vk) =
        Groth16::<Bls12_381>::circuit_specific_setup(
            setup_circuit,
            &mut rng,
        )
        .unwrap();

    let setup_ms = setup_start.elapsed().as_millis();

    let prove_start = Instant::now();

    let proof =
        Groth16::<Bls12_381>::prove(
            &pk,
            prove_circuit,
            &mut rng,
        )
        .unwrap();

    let prove_ms = prove_start.elapsed().as_millis();

    let verify_start = Instant::now();

    let valid =
        Groth16::<Bls12_381>::verify(
            &vk,
            &[],
            &proof,
        )
        .unwrap();

    let verify_ms = verify_start.elapsed().as_millis();

    println!(
        "steps={},run={},seed={},setup_ms={},prove_ms={},verify_ms={},valid={}",
        steps,
        run_id,
        seed,
        setup_ms,
        prove_ms,
        verify_ms,
        valid
    );
}

fn main() {
    let cases = [16384usize, 65536usize];

    for steps in cases {
        for run_id in 1..=3 {
            run_case(steps, run_id);
        }
    }
}
