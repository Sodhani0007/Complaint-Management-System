/**
 * Pre-typed versions of useDispatch/useSelector — every component imports
 * these instead of the raw react-redux hooks, so TypeScript knows the store
 * shape everywhere without each component re-declaring RootState/AppDispatch.
 */

import { useDispatch, useSelector, type TypedUseSelectorHook } from "react-redux";
import type { AppDispatch, RootState } from "../store/store";

export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
