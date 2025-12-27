import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

export default function RAGCore({ active = false }) {
    const coreRef = useRef();
    const linesRef = useRef();

    // Generate neural network nodes
    const { nodes, connections } = useMemo(() => {
        const nodeCount = 60;
        const nodes = [];
        const connections = [];

        // Create nodes in a spherical distribution
        for (let i = 0; i < nodeCount; i++) {
            const phi = Math.acos(-1 + (2 * i) / nodeCount);
            const theta = Math.sqrt(nodeCount * Math.PI) * phi;
            const radius = 1.5 + Math.random() * 0.5;

            nodes.push({
                position: new THREE.Vector3(
                    Math.cos(theta) * Math.sin(phi) * radius,
                    Math.sin(theta) * Math.sin(phi) * radius,
                    Math.cos(phi) * radius
                ),
                size: 0.03 + Math.random() * 0.02
            });
        }

        // Create connections between nearby nodes
        for (let i = 0; i < nodes.length; i++) {
            for (let j = i + 1; j < nodes.length; j++) {
                if (nodes[i].position.distanceTo(nodes[j].position) < 1.2) {
                    connections.push([nodes[i].position, nodes[j].position]);
                }
            }
        }

        return { nodes, connections };
    }, []);

    // Create line geometry
    const lineGeometry = useMemo(() => {
        const geometry = new THREE.BufferGeometry();
        const positions = [];

        connections.forEach(([start, end]) => {
            positions.push(start.x, start.y, start.z);
            positions.push(end.x, end.y, end.z);
        });

        geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
        return geometry;
    }, [connections]);

    useFrame((state) => {
        if (coreRef.current) {
            coreRef.current.rotation.y = state.clock.elapsedTime * 0.1;
            coreRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.05) * 0.1;
        }

        // Pulse effect
        const pulse = Math.sin(state.clock.elapsedTime * 2) * 0.1 + 1;
        if (coreRef.current) {
            coreRef.current.scale.setScalar(active ? pulse * 1.2 : pulse);
        }
    });

    return (
        <group ref={coreRef}>
            {/* Neural network connections */}
            <lineSegments geometry={lineGeometry}>
                <lineBasicMaterial
                    color={active ? "#818cf8" : "#4f46e5"}
                    transparent
                    opacity={0.4}
                />
            </lineSegments>

            {/* Nodes */}
            {nodes.map((node, i) => (
                <mesh key={i} position={node.position}>
                    <sphereGeometry args={[node.size, 8, 8]} />
                    <meshBasicMaterial
                        color={active ? "#a5b4fc" : "#6366f1"}
                        transparent
                        opacity={0.8}
                    />
                </mesh>
            ))}

            {/* Inner glow sphere */}
            <mesh>
                <sphereGeometry args={[0.8, 32, 32]} />
                <meshBasicMaterial
                    color="#4f46e5"
                    transparent
                    opacity={0.15}
                />
            </mesh>

            {/* Core center */}
            <mesh>
                <sphereGeometry args={[0.3, 16, 16]} />
                <meshBasicMaterial
                    color="#818cf8"
                    transparent
                    opacity={0.6}
                />
            </mesh>
        </group>
    );
}
