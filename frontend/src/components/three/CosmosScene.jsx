import { Suspense, useRef } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { Environment, PerspectiveCamera } from '@react-three/drei';
import ParticleField from './ParticleField';
import RAGCore from './RAGCore';
import FloatingRepos from './FloatingRepos';

function CameraRig() {
    const { camera, mouse } = useThree();
    const target = useRef({ x: 0, y: 0 });

    useFrame(() => {
        // Smooth parallax camera movement
        target.current.x += (mouse.x * 0.5 - target.current.x) * 0.05;
        target.current.y += (mouse.y * 0.3 - target.current.y) * 0.05;

        camera.position.x = target.current.x;
        camera.position.y = target.current.y;
        camera.lookAt(0, 0, 0);
    });

    return null;
}

function Scene({ isActive, isWarping }) {
    const groupRef = useRef();

    useFrame((state) => {
        if (groupRef.current) {
            // Warp effect - push scene back and speed up rotation
            if (isWarping) {
                groupRef.current.position.z -= 0.1;
                groupRef.current.rotation.z += 0.02;
            } else {
                // Slowly return to center
                groupRef.current.position.z += (0 - groupRef.current.position.z) * 0.02;
                groupRef.current.rotation.z += (0 - groupRef.current.rotation.z) * 0.02;
            }
        }
    });

    return (
        <group ref={groupRef}>
            <ParticleField count={1500} />
            <RAGCore active={isActive} />
            <FloatingRepos />
        </group>
    );
}

export default function CosmosScene({ isActive = false, isWarping = false, blurred = false }) {
    return (
        <div
            className="cosmos-container"
            style={{
                filter: blurred ? 'blur(8px)' : 'none',
                transform: blurred ? 'scale(1.05)' : 'scale(1)',
                transition: 'filter 0.8s ease, transform 0.8s ease'
            }}
        >
            <Canvas
                gl={{ antialias: true, alpha: true }}
                dpr={[1, 1.5]}
            >
                <PerspectiveCamera makeDefault position={[0, 0, 8]} fov={50} />
                <CameraRig />

                <ambientLight intensity={0.2} />
                <pointLight position={[10, 10, 10]} intensity={0.5} color="#818cf8" />
                <pointLight position={[-10, -10, -10]} intensity={0.3} color="#4f46e5" />

                <Suspense fallback={null}>
                    <Scene isActive={isActive} isWarping={isWarping} />
                </Suspense>

                <fog attach="fog" args={['#050a14', 5, 25]} />
            </Canvas>
        </div>
    );
}
