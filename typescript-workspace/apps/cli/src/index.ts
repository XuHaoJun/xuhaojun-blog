#!/usr/bin/env node
/**
 * Blog Agent CLI entry point
 */

import { Command } from "commander";
import { createProcessCommand } from "./commands/process";
import { createListCommand } from "./commands/list";
import { createRetrieveCommand } from "./commands/retrieve";

const program = new Command();

program
  .name("blog-agent")
  .description("AI Conversation to Blog Agent System CLI")
  .version("0.1.0");

// Add commands
program.addCommand(createProcessCommand());
program.addCommand(createListCommand());
program.addCommand(createRetrieveCommand());

// Parse arguments
program.parse();

