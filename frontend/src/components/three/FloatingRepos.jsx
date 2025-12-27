import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { Float } from '@react-three/drei';

function FloatingIcon({ position, icon, delay = 0 }) {
    const meshRef = useRef();

    useFrame((state) => {
        if (meshRef.current) {
            meshRef.current.rotation.y = state.clock.elapsedTime * 0.3 + delay;
        }
    });

    const colors = {
        python: '#3776ab',
        javascript: '#f7df1e',
        react: '#61dafb',
        typescript: '#3178c6',
        docker: '#2496ed',
        rust: '#dea584'
    };

    return (
        <Float
            speed={1.5}
            rotationIntensity={0.2}
            floatIntensity={0.5}
            floatingRange={[-0.1, 0.1]}
        >
            <group position={position} ref={meshRef}>
                {/* Glass cube */}
                <mesh>
                    <boxGeometry args={[0.4, 0.4, 0.4]} />
                    <meshPhysicalMaterial
                        color={colors[icon] || '#6366f1'}
                        transparent
                        opacity={0.3}
                        roughness={0.1}
                        metalness={0.1}
                        envMapIntensity={0.5}
                    />
                </mesh>

                {/* Inner glow */}
                <mesh>
                    <boxGeometry args={[0.25, 0.25, 0.25]} />
                    <meshBasicMaterial
                        color={colors[icon] || '#6366f1'}
                        transparent
                        opacity={0.6}
                    />
                </mesh>
            </group>
        </Float>
    );
}

export default function FloatingRepos() {
    const icons = [
        { icon: 'python', position: [3, 1.5, -1] },
        { icon: 'javascript', position: [-3, 0.5, 0.5] },
        { icon: 'react', position: [2.5, -1, 1] },
        { icon: 'typescript', position: [-2, 1.5, -1.5] },
        { icon: 'docker', position: [1, 2, 2] },
        { icon: 'rust', position: [-1.5, -1.5, 1.5] }
    ];

    return (
        <group>
            {icons.map((item, i) => (
                <FloatingIcon
                    key={i}
                    icon={item.icon}
                    position={item.position}
                    delay={i * 0.5}
                />
            ))}
        </group>
    );
}
