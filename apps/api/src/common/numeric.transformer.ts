import { ValueTransformer } from 'typeorm';

/** Postgres NUMERIC llega como string a Node; lo convertimos a number. */
export const numericTransformer: ValueTransformer = {
  to: (value?: number | null) => value,
  from: (value?: string | null) => (value === null || value === undefined ? value : parseFloat(value)),
};
