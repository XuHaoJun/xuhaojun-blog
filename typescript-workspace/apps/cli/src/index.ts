#!/usr/bin/env node
/**
 * Blog Agent CLI entry point
 */

import { Command } from "commander";
import { createProcessCommand } from "./commands/process";

const program = new Command();

program
  .name("blog-agent")
  .description("AI Conversation to Blog Agent System CLI")
  .version("0.1.0");

// Add commands
program.addCommand(createProcessCommand());

// Parse arguments
program.parse();

