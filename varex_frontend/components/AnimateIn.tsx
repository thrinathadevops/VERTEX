"use client";

import { motion, type Variants } from "framer-motion";
import { type ReactNode } from "react";
import { useReducedMotion } from "framer-motion";

interface AnimateInProps {
    children: ReactNode;
    className?: string;
    delay?: number;
    direction?: "up" | "down" | "left" | "right" | "none";
    duration?: number;
    once?: boolean;
    trigger?: "inView" | "mount";
    distance?: number;
}

const getVariants = (direction: string, duration: number, distance: number): Variants => {
    const directions: Record<string, { x?: number; y?: number }> = {
        up: { y: distance },
        down: { y: -distance },
        left: { x: distance },
        right: { x: -distance },
        none: {},
    };

    return {
        hidden: { opacity: 0, ...directions[direction], filter: "blur(10px)" },
        visible: {
            opacity: 1,
            x: 0,
            y: 0,
            filter: "blur(0px)",
            transition: { duration, ease: [0.16, 1, 0.3, 1] },
        },
    };
};

export default function AnimateIn({
    children,
    className = "",
    delay = 0,
    direction = "up",
    duration = 0.6,
    once = true,
    trigger = "inView",
    distance = 28,
}: AnimateInProps) {
    const reduceMotion = useReducedMotion();
    const shouldAnimateOnMount = trigger === "mount";

    return (
        <motion.div
            variants={reduceMotion ? getVariants("none", 0.01, 0) : getVariants(direction, duration, distance)}
            initial="hidden"
            animate={shouldAnimateOnMount ? "visible" : undefined}
            whileInView={shouldAnimateOnMount ? undefined : "visible"}
            viewport={shouldAnimateOnMount ? undefined : { once, margin: "-64px", amount: 0.18 }}
            transition={{ delay }}
            className={className}
        >
            {children}
        </motion.div>
    );
}

/* Stagger container for children */
export function StaggerContainer({
    children,
    className = "",
    staggerDelay = 0.08,
    delayChildren = 0.12,
}: {
    children: ReactNode;
    className?: string;
    staggerDelay?: number;
    delayChildren?: number;
}) {
    const reduceMotion = useReducedMotion();
    return (
        <motion.div
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: "-64px", amount: 0.18 }}
            variants={{
                hidden: {},
                visible: {
                    transition: {
                        staggerChildren: reduceMotion ? 0 : staggerDelay,
                        delayChildren: reduceMotion ? 0 : delayChildren,
                    },
                },
            }}
            className={className}
        >
            {children}
        </motion.div>
    );
}

export function StaggerItem({
    children,
    className = "",
}: {
    children: ReactNode;
    className?: string;
}) {
    const reduceMotion = useReducedMotion();
    return (
        <motion.div
            variants={{
                hidden: reduceMotion ? { opacity: 0 } : { opacity: 0, y: 22, filter: "blur(8px)" },
                visible: {
                    opacity: 1,
                    y: 0,
                    filter: "blur(0px)",
                    transition: { duration: reduceMotion ? 0.01 : 0.45, ease: [0.16, 1, 0.3, 1] },
                },
            }}
            className={className}
        >
            {children}
        </motion.div>
    );
}
