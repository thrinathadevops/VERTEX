"use client";

import { motion, type Variants } from "framer-motion";

const SPRING = { type: "spring" as const, stiffness: 200, damping: 22 };

const containerVariants: Variants = {
    hidden:  {},
    visible: { transition: { staggerChildren: 0.12 } },
};

const itemVariant: Variants = {
    hidden:  { opacity: 0, y: -16 },
    visible: { opacity: 1, y: 0, transition: SPRING },
};

export default function AnimatedHeader() {
    return (
        <motion.div
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="flex items-center space-x-3 mb-8"
        >
            {/* Floating logo icon */}
            <motion.div
                variants={itemVariant}
                animate={{ y: [0, -5, 0] }}
                transition={{ y: { duration: 3, repeat: Infinity, ease: "easeInOut" } }}
                className="bg-indigo-600 p-2 rounded-lg shadow-lg shadow-indigo-500/30"
            >
                <svg className="w-6 h-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
            </motion.div>

            {/* Title */}
            <motion.h1 variants={itemVariant} className="text-2xl font-bold text-gray-900 dark:text-white">
                VAREX{" "}
                <motion.span
                    className="text-indigo-600 dark:text-indigo-400 inline-block"
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.3, ...SPRING }}
                >
                    DriftGuard
                </motion.span>
            </motion.h1>
        </motion.div>
    );
}
