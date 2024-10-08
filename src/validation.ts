import { chain, gather, uri, type ASNode } from "./model";

export type FieldConstraintName = keyof typeof fieldConstraints;
export type FieldConstraint = (name: string, value: any) => void;

export interface Validator {
  type?: string | string[],
  properties?: Record<string, FieldConstraintName[] | FieldConstraintName | FieldConstraint>
}

export interface ValidationItem {
  path: string,
  value: any,
  message: string
}

export function validate(value: any, schema: Validator) {
  if (isEmpty(value)) throw new ValidationError([{ path: '', value: value, message: 'must be defined' }]);

  let errors: ValidationItem[] = [];
  if (Array.isArray(value)) {
    let index = 0;
    for (let obj of value) {
      try {
        validateSingle(index.toString(), obj, schema);
      } catch (e: any) {
        if (e instanceof ValidationError)
          errors = errors.concat(e.items);
        else {
          errors.push({ path: index.toString(), value: obj, message: e.message });
        }
      }
      index++;
    }
  } else {
    try {
      validateSingle('', value, value);
    } catch (e: any) {
      if (e instanceof ValidationError)
        errors = errors.concat(e.items);
      else {
        errors.push({ path: '', value: value, message: e.message });
      }
    }
  }

  if (errors.length) throw new ValidationError(errors);
}

function validateSingle(path: string, value: any, schema: Validator) {
  if (typeof value !== 'object') throw new Error('must be an object');

  if (schema.type) {
    if (!intersection(schema.type, value.type).length)
      throw new Error(`must be type - ${schema.type}`);
  }

  let errors: ValidationItem[] = [];
  /*if (schema.properties) {
    for (let field in schema.properties) {
      let constraints = schema.properties[field];
      for (let constraint in constraints) {
        fieldConstraints[constraint](field, value);
      }
    }
  }*/

  if (errors.length) throw new ValidationError(errors);
}

export class ValidationError extends Error {
  constructor(public items: ValidationItem[]) {
    super('validation errors');
  }
}

function intersection(a: any, b: any) {
  b = gather(b);
  a = gather(a);
  return a.filter((item: any) => b.includes(item));
}

function joinName(...path: string[]) {
  return path.filter(p => !!p).join('.');
}

function isEmpty(value: any) {
  return value === undefined || value === null || value === '' || (Array.isArray(value) && value.length === 0);
}

export function required(name: string, value: any) {
  if (isEmpty(value)) throw new Error('property is required');
}

export function functional(name: string, value: any) {
  if (gather(value).length > 1) throw new Error('property cannot have multiple values');
}

export function number(name: string, value: any) {
  for (let obj of chain(value)) {
    if (typeof obj !== 'number') throw new Error('property must be a number');
  }
}

export function string(name: string, value: any) {
  for (let obj of chain(value)) {
    if (typeof obj !== 'string') throw new Error('property must be a string');
  }
}

export function identifiable(name: string, value: any) {
  for (let obj of chain<ASNode>(value)) {
    if (!uri(obj)) throw new Error('property must have a URI, either as a string, an object with an id, or a link with a href');
  }
}

export const fieldConstraints: Record<string, FieldConstraint> = {
  required,
  functional,
  number,
  string,
  identifiable
}