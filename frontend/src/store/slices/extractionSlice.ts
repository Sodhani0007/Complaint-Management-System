/**
 * Owns the AI extraction lifecycle only: uploading -> extracting -> done/error.
 * Deliberately does NOT own the form's editable values — once extraction
 * completes, complaintSlice takes over as the source of truth for anything
 * the user can edit. Merging these two slices would make it ambiguous
 * whether a field displayed in the form is "what the AI said" or "what the
 * user changed", which defeats the whole human-in-the-loop design.
 */

import { createAsyncThunk, createSlice, type PayloadAction } from "@reduxjs/toolkit";
import { extractErrorMessage, extractFromFile, extractFromText } from "../../api/client";
import type { ExtractedFields } from "../../types/complaint";

export type ExtractionStatus = "idle" | "extracting" | "done" | "error";

interface ExtractionState {
  status: ExtractionStatus;
  extractionId: string | null;
  confidenceScore: number | null;
  modelUsed: string | null;
  missingRequiredFields: string[];
  errorMessage: string | null;
}

const initialState: ExtractionState = {
  status: "idle",
  extractionId: null,
  confidenceScore: null,
  modelUsed: null,
  missingRequiredFields: [],
  errorMessage: null,
};

export const runFileExtraction = createAsyncThunk<
  { fields: ExtractedFields; extractionId: string; confidence: number; model: string; missing: string[] },
  File,
  { rejectValue: string }
>("extraction/fromFile", async (file, { rejectWithValue }) => {
  try {
    const result = await extractFromFile(file);
    return {
      fields: result.fields,
      extractionId: result.extraction_id,
      confidence: result.confidence_score,
      model: result.model_used,
      missing: result.missing_required_fields,
    };
  } catch (err) {
    return rejectWithValue(extractErrorMessage(err));
  }
});

export const runTextExtraction = createAsyncThunk<
  { fields: ExtractedFields; extractionId: string; confidence: number; model: string; missing: string[] },
  string,
  { rejectValue: string }
>("extraction/fromText", async (text, { rejectWithValue }) => {
  try {
    const result = await extractFromText(text);
    return {
      fields: result.fields,
      extractionId: result.extraction_id,
      confidence: result.confidence_score,
      model: result.model_used,
      missing: result.missing_required_fields,
    };
  } catch (err) {
    return rejectWithValue(extractErrorMessage(err));
  }
});

const extractionSlice = createSlice({
  name: "extraction",
  initialState,
  reducers: {
    resetExtraction: () => initialState,
  },
  extraReducers: (builder) => {
    builder
      .addCase(runFileExtraction.pending, (state) => {
        state.status = "extracting";
        state.errorMessage = null;
      })
      .addCase(runFileExtraction.fulfilled, (state, action) => {
        state.status = "done";
        state.extractionId = action.payload.extractionId;
        state.confidenceScore = action.payload.confidence;
        state.modelUsed = action.payload.model;
        state.missingRequiredFields = action.payload.missing;
      })
      .addCase(runFileExtraction.rejected, (state, action: PayloadAction<string | undefined>) => {
        state.status = "error";
        state.errorMessage = action.payload ?? "Extraction failed";
      })
      .addCase(runTextExtraction.pending, (state) => {
        state.status = "extracting";
        state.errorMessage = null;
      })
      .addCase(runTextExtraction.fulfilled, (state, action) => {
        state.status = "done";
        state.extractionId = action.payload.extractionId;
        state.confidenceScore = action.payload.confidence;
        state.modelUsed = action.payload.model;
        state.missingRequiredFields = action.payload.missing;
      })
      .addCase(runTextExtraction.rejected, (state, action: PayloadAction<string | undefined>) => {
        state.status = "error";
        state.errorMessage = action.payload ?? "Extraction failed";
      });
  },
});

export const { resetExtraction } = extractionSlice.actions;
export default extractionSlice.reducer;
