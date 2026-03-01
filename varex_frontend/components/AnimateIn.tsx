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
}

const getVariants = (direction: string, duration: number): Variants => {
    const directions: Record<string, { x?: number; y?: number }> = {
        up: { y: 40 },
        down: { y: -40 },
        left: { x: 40 },
        right: { x: -40 },
        none: {},
    };

    return {
        hidden: { opacity: 0, ...directions[direction] },
        visible: {
            opacity: 1,
            x: 0,
            y: 0,
            transition: { duration, ease: [0.25, 0.4, 0.25, 1] },
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
}: AnimateInProps) {
    const reduceMotion = useReducedMotion();
    const shouldAnimateOnMount = trigger === "mount";

    return (
        <motion.div
            variants={reduceMotion ? getVariants("none", 0.01) : getVariants(direction, duration)}
            initial="hidden"
            animate={shouldAnimateOnMount ? "visible" : undefined}
            whileInView={shouldAnimateOnMount ? undefined : "visible"}
            viewport={shouldAnimateOnMount ? undefined : { once, margin: "-50px" }}
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
    staggerDelay = 0.1,
    delayChildren = 0.2,
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
            viewport={{ once: true, margin: "-50px" }}
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
                hidden: reduceMotion ? { opacity: 0 } : { opacity: 0, y: 30 },
                visible: {
                    opacity: 1,
                    y: 0,
                    transition: { duration: reduceMotion ? 0.01 : 0.5, ease: [0.25, 0.4, 0.25, 1] },
                },
            }}
            className={className}
        >
            {children}
        </motion.div>
    );
}
