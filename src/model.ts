export type ASNode = ASLink | ASObject | string;
export type Content = string[] | { [key: string]: string };
export type Timestamp = string;

export interface ASLink {
  id?: string;
  type?: string[];

  href: string;
  rel?: string;
  mediaType?: string;
  name?: Content;
  hreflang?: string;
  height?: number;
  width?: number;
  preview?: ASNode[];

  //
  [key: string]: any;
}

export interface ASObject {
  id?: string;
  type?: string[];

  // Content
  content?: Content;
  name?: Content;
  summary?: Content;

  // Relation
  attachment?: ASNode[];
  attributedTo?: ASNode[];
  audience?: ASNode[];
  context?: ASNode[];
  generator?: ASNode[];
  icon?: ASNode[];
  image?: ASNode[];
  inReplyTo?: ASNode[];
  location?: ASNode[];
  preview?: ASNode[];
  replies?: ASNode[];
  tag?: ASNode[];
  url?: ASNode[];

  // Delivery
  to?: ASNode[];
  bto?: ASNode[];
  cc?: ASNode[];
  bcc?: ASNode[];

  // Functional
  duration?: Timestamp;
  endTime?: Timestamp;
  mediaType?: Timestamp;
  published?: Timestamp;
  startTime?: Timestamp;
  updated?: Timestamp;

  //
  [key: string]: any;
}

export interface Collection<T = ASNode> extends ASObject {
  totalItems?: number;
  current?: ASNode;
  first?: ASNode;
  last?: ASNode;
  items?: T[];
}

export interface CollectionPage<T = ASNode> extends Collection<T> {
  partOf?: ASNode;
  next?: ASNode;
  prev?: ASNode;
  startIndex?: number;
}

export interface Activity extends ASObject {
  actor?: ASNode[];
  object?: ASNode[];
  target?: ASNode[];
  result?: ASNode[];
  origin?: ASNode[];
  instrument?: ASNode[];

  // Extension
  processed?: Timestamp;
}

export interface Tombstone extends ASObject {
  type: ['Tombstone'];
  formerType?: string[];
  deleted?: Timestamp;
}

export function expand(value: ASNode): ASObject | ASLink {
  if (typeof value === 'string') {
    return { id: value };
  }
  return value;
}

export function compact(value: ASObject | ASLink): Record<string, any> | string | undefined {
  let keys = Object.keys(value);
  if (keys.length === 0) return undefined;
  if (keys.length === 1 && keys[0] === 'id') {
    return value.id;
  }
  return value;
}

export function many(value: any) {
  if (Array.isArray(value)) {
    return value;
  }
  return value;
}

export function* chain<T>(...args: any[]): IterableIterator<T> {
  for (let arg of args) {
    if (Array.isArray(arg)) {
      yield* chain<T>(...arg);
    } else if (arg === undefined) {
      continue;
    } else {
      yield arg as T;
    }
  }
}

export function gather<T>(...args: any[]): T[] {
  return Array.from(chain<T>(...args));
}

export function* chainNodes(...args: any[]): IterableIterator<ASNode> {
  for (let arg of args) {
    if (Array.isArray(arg)) {
      yield* chainNodes(...arg);
    } else if (arg === undefined) {
      continue;
    } else {
      yield expand(arg);
    }
  }
}

export function gatherNodes(...args: any[]): ASNode[] {
  return Array.from(chainNodes(...args));
}

export function first<T>(...args: any[]): T | undefined {
  return chain<T>(...args).next().value;
}

export function uri(node: ASNode): string | undefined {
  if (!node) return undefined;
  if (typeof node === 'string') {
    return node;
  }
  if (typeof node.href === 'string') {
    return node.href;
  }
  return node.id!;
}