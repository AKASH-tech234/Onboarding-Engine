import { cn } from "../utils/cn";
import { motion } from "framer-motion";

export const TypewriterEffectSmooth = ({ words, className, cursorClassName }) => {
  const wordsArray = words.map((word) => ({ ...word, text: word.text.split("") }));
  
  const renderWords = () => {
    return (
      <div className="flex">
        {wordsArray.map((word, idx) => (
          <div key={`word-${idx}`} className="inline-block mr-2">
            {word.text.map((char, index) => (
              <span key={`char-${index}`} className={cn("text-white", word.className)}>
                {char}
              </span>
            ))}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className={cn("flex space-x-1 justify-center my-6", className)}>
      <motion.div
        className="overflow-hidden pb-2"
        initial={{ scaleX: 0 }}
        style={{ transformOrigin: "left" }}
        whileInView={{ scaleX: 1 }}
        transition={{ duration: 1.5, ease: "linear", delay: 0.5 }}
      >
        <div className="text-xl sm:text-2xl md:text-3xl lg:text-4xl font-bold" style={{ whiteSpace: "nowrap" }}>
          {renderWords()}
        </div>
      </motion.div>
      <motion.span
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.8, repeat: Infinity, repeatType: "reverse" }}
        className={cn("block rounded-sm w-[4px] h-6 sm:h-8 lg:h-10 bg-blue-500", cursorClassName)}
      ></motion.span>
    </div>
  );
};
