import { Canvas, useThree } from "@react-three/fiber";
import { useEffect, useMemo } from "react";
import { Color, DoubleSide } from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

import type { PlottedConnection, PlottedNote } from "./graph";

interface SceneProps {
  points: PlottedNote[];
  connections: PlottedConnection[];
  onNote: (ref: string) => void;
  onHover: (note: PlottedNote | null) => void;
  onUnavailable: () => void;
}

type Position = [number, number, number];

function position({ x, y, z }: PlottedNote): Position {
  return [(x - 360) / 84, (169 - y) / 84, z];
}

function CameraControls({ onHover, onUnavailable }: Pick<SceneProps, "onHover" | "onUnavailable">) {
  const { camera, gl, invalidate } = useThree();
  useEffect(() => {
    const canvas = gl.domElement;
    const controls = new OrbitControls(camera, canvas);
    controls.enableDamping = false;
    controls.enablePan = false;
    controls.enableZoom = false;
    controls.rotateSpeed = 0.65;
    controls.minPolarAngle = Math.PI / 5;
    controls.maxPolarAngle = Math.PI * 4 / 5;
    canvas.style.touchAction = "pan-y";
    controls.update();

    const clear = () => onHover(null);
    const redraw = () => invalidate();
    const lost = (event: Event) => {
      event.preventDefault();
      onUnavailable();
    };
    controls.addEventListener("start", clear);
    controls.addEventListener("change", redraw);
    canvas.addEventListener("pointerleave", clear);
    canvas.addEventListener("webglcontextlost", lost);
    return () => {
      controls.removeEventListener("start", clear);
      controls.removeEventListener("change", redraw);
      canvas.removeEventListener("pointerleave", clear);
      canvas.removeEventListener("webglcontextlost", lost);
      controls.dispose();
    };
  }, [camera, gl, invalidate, onHover, onUnavailable]);
  return null;
}

function Constellation() {
  const stars = useMemo(() => Float32Array.from(Array.from({ length: 176 }, (_, i) => [
    7.4 * Math.sin(i * 13.807),
    3.5 * Math.cos(i * 2.956),
    -2.2 + 2.6 * Math.sin(i * 4.067),
  ]).flat()), []);
  return (
    <>
      <points>
        <bufferGeometry><bufferAttribute attach="attributes-position" args={[stars, 3]} /></bufferGeometry>
        <pointsMaterial size={0.025} color="#a9be9b" opacity={0.48} transparent depthWrite={false} />
      </points>
      <group position={[0, 0, -0.9]} rotation={[0.2, -0.12, 0]}>
        {[1.34, 2.18, 3.08, 3.89].map((radius) => (
          <mesh key={radius} scale={[1, 0.58, 1]}>
            <ringGeometry args={[radius, radius + 0.008, 100]} />
            <meshBasicMaterial color="#95bd83" opacity={0.31} transparent depthWrite={false} side={DoubleSide} />
          </mesh>
        ))}
      </group>
    </>
  );
}

function ConnectionLines({ connections }: Pick<SceneProps, "connections">) {
  const { vertices, colors } = useMemo(() => {
    const coordinates: number[] = [];
    const rgb: number[] = [];
    for (const { source, target, edge } of connections) {
      const color = new Color(edge.type === "contradicts" ? "#d6a586" : "#a9ca9a");
      coordinates.push(...position(source), ...position(target));
      rgb.push(color.r, color.g, color.b, color.r, color.g, color.b);
    }
    return { vertices: new Float32Array(coordinates), colors: new Float32Array(rgb) };
  }, [connections]);

  return (
    <lineSegments>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" args={[vertices, 3]} />
        <bufferAttribute attach="attributes-color" args={[colors, 3]} />
      </bufferGeometry>
      <lineBasicMaterial vertexColors opacity={0.55} transparent />
    </lineSegments>
  );
}

function NoteNode({ point, onNote, onHover }: Pick<SceneProps, "onNote" | "onHover"> & { point: PlottedNote }) {
  const size = point.focus ? 0.21 : 0.135;
  return (
    <group
      position={position(point)}
      onPointerOver={(event) => {
        event.stopPropagation();
        onHover(point);
      }}
      onPointerOut={() => onHover(null)}
      onClick={(event) => {
        event.stopPropagation();
        if (event.delta <= 4) onNote(point.ref);
      }}
    >
      <mesh>
        <sphereGeometry args={[size, 24, 16]} />
        <meshStandardMaterial color={point.color} emissive={point.color} emissiveIntensity={0.52} roughness={0.4} />
      </mesh>
      <mesh>
        <sphereGeometry args={[size * 2.15, 20, 10]} />
        <meshBasicMaterial color={point.color} opacity={point.focus ? 0.16 : 0.09} transparent depthWrite={false} />
      </mesh>
      <mesh rotation={[0.3, 0.2, 0]}>
        <ringGeometry args={[size * 1.64, size * 1.71, 64]} />
        <meshBasicMaterial color={point.color} opacity={0.7} transparent depthWrite={false} side={DoubleSide} />
      </mesh>
    </group>
  );
}

export default function GraphScene({ points, connections, onNote, onHover, onUnavailable }: SceneProps) {
  return (
    <Canvas
      className="garden-atlas__scene"
      aria-hidden="true"
      frameloop="demand"
      dpr={[1, 1.5]}
      gl={{ antialias: true, powerPreference: "low-power" }}
      camera={{ position: [0, 1.24, 7.8], fov: 38, near: 0.1, far: 34 }}
      fallback={<div>3D is unavailable on this device.</div>}
    >
      <ambientLight intensity={1.05} />
      <pointLight position={[-1.8, 3.5, 4]} intensity={9} color="#d7edb9" />
      <CameraControls onHover={onHover} onUnavailable={onUnavailable} />
      <Constellation />
      <ConnectionLines connections={connections} />
      {points.map((point) => <NoteNode key={point.ref} point={point} onNote={onNote} onHover={onHover} />)}
    </Canvas>
  );
}
