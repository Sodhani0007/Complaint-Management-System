/**
 * Owns the actual form-of-record: the editable field values (whether
 * populated by AI extraction or typed by hand) and the save lifecycle.
 * `populateFromExtraction` and manual `updateField` calls both write to the
 * same `fields` object — from the form's perspective there's no difference
 * between "AI filled this" and "I typed this" once it's in state, which is
 * exactly the point: the human can freely overwrite AI output.
 */

import { createAsyncThunk, createSlice, type PayloadAction } from "@reduxjs/toolkit";
import { extractErrorMessage, saveComplaint } from "../../api/client";
import type { ComplaintCreatePayload, ComplaintRead, ExtractedFields } from "../../types/complaint";
import { emptyComplaintFields } from "../../types/complaint";

export type SaveStatus = "idle" | "saving" | "saved" | "error";

interface ComplaintState {
  fields: ExtractedFields;
  saveStatus: SaveStatus;
  savedComplaint: ComplaintRead | null;
  errorMessage: string | null;
}

const initialState: ComplaintState = {
  fields: emptyComplaintFields(),
  saveStatus: "idle",
  savedComplaint: null,
  errorMessage: null,
};

export const submitComplaint = createAsyncThunk<
  ComplaintRead,
  { extractionSnapshot?: Record<string, unknown> | null; modelUsed?: string | null; confidence?: number | null },
  { state: { complaint: ComplaintState }; rejectValue: string }
>("complaint/submit", async ({ extractionSnapshot, modelUsed, confidence }, { getState, rejectWithValue }) => {
  const { fields } = getState().complaint;

  if (!fields.product_name || !fields.batch_lot_number || !fields.description) {
    return rejectWithValue("Product name, batch/lot number, and description are required.");
  }

  const payload: ComplaintCreatePayload = {
    product_name: fields.product_name,
    batch_lot_number: fields.batch_lot_number,
    description: fields.description,
    complaint_source: fields.complaint_source,
    customer_name: fields.customer_name,
    complaint_type: fields.complaint_type,
    complaint_date: fields.complaint_date,
    manufacturing_date: fields.manufacturing_date,
    expiry_date: fields.expiry_date,
    quantity_affected: fields.quantity_affected,
    severity: fields.initial_severity,
    priority: fields.priority,
    ai_extraction_snapshot: extractionSnapshot ?? null,
    ai_model_used: modelUsed ?? null,
    ai_confidence: confidence ?? null,
  };

  try {
    return await saveComplaint(payload);
  } catch (err) {
    return rejectWithValue(extractErrorMessage(err));
  }
});

const complaintSlice = createSlice({
  name: "complaint",
  initialState,
  reducers: {
    populateFromExtraction: (state, action: PayloadAction<ExtractedFields>) => {
      state.fields = action.payload;
    },
    updateField: (state, action: PayloadAction<{ field: keyof ExtractedFields; value: string | number | null }>) => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      (state.fields as any)[action.payload.field] = action.payload.value;
    },
    resetForm: (state) => {
      state.fields = emptyComplaintFields();
      state.saveStatus = "idle";
      state.savedComplaint = null;
      state.errorMessage = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(submitComplaint.pending, (state) => {
        state.saveStatus = "saving";
        state.errorMessage = null;
      })
      .addCase(submitComplaint.fulfilled, (state, action) => {
        state.saveStatus = "saved";
        state.savedComplaint = action.payload;
      })
      .addCase(submitComplaint.rejected, (state, action: PayloadAction<string | undefined>) => {
        state.saveStatus = "error";
        state.errorMessage = action.payload ?? "Failed to save complaint";
      });
  },
});

export const { populateFromExtraction, updateField, resetForm } = complaintSlice.actions;
export default complaintSlice.reducer;
