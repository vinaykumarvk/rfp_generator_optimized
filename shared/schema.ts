import { pgTable, text, serial, integer, boolean, date, timestamp, foreignKey, real, pgEnum } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";
import { relations } from "drizzle-orm";

export const users = pgTable("users", {
  id: serial("id").primaryKey(),
  username: text("username").notNull().unique(),
  password: text("password").notNull(),
});

export const rfpResponses = pgTable("rfp_responses", {
  id: serial("id").primaryKey(),
  clientName: text("client_name").notNull(),
  clientIndustry: text("client_industry").notNull(),
  rfpTitle: text("rfp_title").notNull(),
  rfpId: text("rfp_id"),
  submissionDate: date("submission_date").notNull(),
  budgetRange: text("budget_range"),
  projectSummary: text("project_summary").notNull(),
  companyName: text("company_name").notNull(),
  pointOfContact: text("point_of_contact").notNull(),
  companyStrengths: text("company_strengths"),
  selectedTemplate: text("selected_template").notNull(),
  customizations: text("customizations"),
  generatedContent: text("generated_content"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  lastUpdated: timestamp("last_updated").defaultNow().notNull(),
});

export const excelRequirementResponses = pgTable("excel_requirement_responses", {
  id: serial("id").primaryKey(),
  // New fields for RFP identification
  rfpName: text("rfp_name"),
  requirementId: text("requirement_id"),
  uploadedBy: text("uploaded_by"),
  
  // Existing fields
  category: text("category").notNull(),
  requirement: text("requirement").notNull(),
  
  // Response fields
  finalResponse: text("final_response"),
  openaiResponse: text("openai_response"),
  anthropicResponse: text("anthropic_response"),
  deepseekResponse: text("deepseek_response"),
  moaResponse: text("moa_response"),
  
  // Similar questions (stored as JSON string)
  similarQuestions: text("similar_questions"),
  
  // Metadata
  timestamp: timestamp("timestamp").defaultNow().notNull(),
  rating: integer("rating"),
  feedback: text("feedback"),  // 'positive', 'negative', or null
  modelProvider: text("model_provider"),
});

// Table for storing reference information
export const referenceResponses = pgTable("reference_responses", {
  id: serial("id").primaryKey(),
  // Link to the parent response
  responseId: integer("response_id").notNull().references(() => excelRequirementResponses.id, { onDelete: 'cascade' }),
  // Reference information
  category: text("category").notNull(),
  requirement: text("requirement").notNull(),
  response: text("response").notNull(),
  reference: text("reference"),
  score: real("score").notNull(),
  timestamp: timestamp("timestamp").defaultNow().notNull(),
});

// Relations definition
export const excelRequirementResponsesRelations = relations(excelRequirementResponses, ({ many }) => ({
  references: many(referenceResponses),
}));

export const referenceResponsesRelations = relations(referenceResponses, ({ one }) => ({
  parentResponse: one(excelRequirementResponses, {
    fields: [referenceResponses.responseId],
    references: [excelRequirementResponses.id],
  }),
}));

// Insert schemas
export const insertUserSchema = createInsertSchema(users).pick({
  username: true,
  password: true,
});

export const insertRfpResponseSchema = createInsertSchema(rfpResponses).omit({
  id: true,
  createdAt: true,
  lastUpdated: true,
});

export const insertExcelRequirementResponseSchema = createInsertSchema(excelRequirementResponses).omit({
  id: true,
  timestamp: true,
});

export const insertReferenceResponseSchema = createInsertSchema(referenceResponses).omit({
  id: true,
  timestamp: true,
});

// Types
export type InsertUser = z.infer<typeof insertUserSchema>;
export type User = typeof users.$inferSelect;

export type InsertRfpResponse = z.infer<typeof insertRfpResponseSchema>;
export type RfpResponse = typeof rfpResponses.$inferSelect;

export type InsertExcelRequirementResponse = z.infer<typeof insertExcelRequirementResponseSchema>;
export type ExcelRequirementResponse = typeof excelRequirementResponses.$inferSelect;

export type InsertReferenceResponse = z.infer<typeof insertReferenceResponseSchema>;
export type ReferenceResponse = typeof referenceResponses.$inferSelect;

// Template types for frontend
export const templateSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  suitableFor: z.array(z.string()),
  structure: z.array(z.string()),
});

export type Template = z.infer<typeof templateSchema>;

// Embeddings table schema - We'll create this using raw SQL since we need pgvector
export const embeddings = pgTable("embeddings", {
  id: serial("id").primaryKey(),
  // Metadata fields
  category: text("category").notNull(),
  requirement: text("requirement").notNull(), 
  response: text("response").notNull(),
  reference: text("reference"),
  // Store other payload data as JSON
  payload: text("payload").notNull(), // JSON string of additional data
  // Note: The vector field will be created using raw SQL, we just define it here for type-safety
  // but exclude it from the create table operation
  // Timestamp for when this embedding was created
  timestamp: timestamp("timestamp").defaultNow().notNull(),
});

// Insert schema for embeddings
export const insertEmbeddingSchema = createInsertSchema(embeddings).omit({
  id: true,
  timestamp: true,
});

// Types
export type InsertEmbedding = z.infer<typeof insertEmbeddingSchema> & { embedding: number[] };
export type Embedding = typeof embeddings.$inferSelect & { embedding: number[] };
