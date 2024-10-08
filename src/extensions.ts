import type { ASNode, ASObject, Activity, Collection } from "./model";

export interface Extension extends ASObject {
  features?: Collection<Feature>;
  types?: Collection<Type>;
  properties?: Collection<Property>;
  functions?: Collection<Function>;
  prefixes?: Record<string, string>;

  depends?: ASNode[];
}

export interface Feature extends ASObject {
  rules?: Collection<Rule>;
}

export interface Rule extends ASObject {
  matchAny?: Activity[];
  function?: ASNode[];
  example?: Example[];
}

export interface Example extends ASObject {
  given?: ASObject[];
  when?: Activity[];
  then?: ASObject[];
}

export interface Property extends ASObject {
  range?: string[];  // ids of types
}

export interface Test extends ASObject {
  mock?: ASObject[];
  input?: ASObject[];
  output?: ASObject[];
}

export interface Function extends ASObject {
  input?: Property[];
  output?: Property[];
  tests?: Test[];
}

export interface Type extends ASObject {
  extends?: ASNode[];
  collectionMap?: Record<string, string[]>;   // /endpoint => ['Collection', 'Type']
  properties?: ASNode[];
}

