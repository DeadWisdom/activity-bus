import { chain, gather, type ASObject, type Activity } from "./model";

export type RuleFunction = (act: Activity) => Promise<Activity | void>;

export interface Rule extends ASObject {
  target?: ASObject[];
}

export interface RuleConfig extends Omit<Rule, 'content'> {
  content: RuleFunction;
}

let rules: Rule[] = [];

export function rule(r: RuleConfig) {
  let content = gather(r.content).map(c => {
    return '';
  });
  rules.push({ ...r, content });
}

function matchObjects(ruleTarget: ASObject, activityTarget: ASObject): boolean {
  // Objects must have matching values for every key
  for (const key in ruleTarget) {
    const ruleValue = ruleTarget[key];
    const activityValue = activityTarget[key];

    if (!match(ruleValue, activityValue)) return false;
  }
  return true;
}

function matchLists(ruleValue: any, activityValue: any): boolean {
  // At least one item in the rule list must match an item in the activityValue list or the activityValue itself (since it's chained)
  for (const ruleItem of chain(ruleValue)) {
    for (const activityItem of chain(activityValue)) {
      if (match(ruleItem, activityItem)) {
        return true;
      }
    }
  }
  return false;
}

function match(ruleValue: any, activityValue: any): boolean {
  if (Array.isArray(ruleValue)) {
    return matchLists(ruleValue, activityValue);
  }
  if (typeof ruleValue === 'object') {
    return matchObjects(ruleValue, activityValue);
  }
  return ruleValue === activityValue;
}


// Function to process an activity through the rules
export function* chainRules(activity: Activity) {
  for (const rule of rules) {
    if (rule.target) {
      // Check if any of the rule's target objects match the activity
      const matchingTarget = rule.target.some(target => match(target, activity));
      if (matchingTarget) {
        yield rule;
      }
    } else {
      yield rule;
    }
  }
}

export async function applyRules(activity: Activity) {
  for (const rule of chainRules(activity)) {
    console.log('->', rule.summary);
  }
}


/* Builtin Rules */

rule({
  summary: 'Log when anything is created',
  target: [{
    type: ['Create']
  }],
  content: async (act: Activity) => {
    console.log('SOMEONE CREATED SOMETHING!', act);
  }
});


rule({
  summary: 'Log when a note is created',
  target: [{
    type: ['Create'],
    object: [
      { type: ['Note'] }
    ]
  }],
  content: async (act: Activity) => {
    console.log('SOMEONE CREATED A NOTE!', act);
  }
});

rule({
  summary: 'Log when a pigeon is created',
  target: [{
    type: ['Create'],
    object: [
      { type: ['Pigeon'] }
    ]
  }],
  content: async (act: Activity) => {
    console.log('SOMEONE CREATED A PIGEON!', act);
  }
});

rule({
  summary: 'Log when a note is moved',
  target: [{
    type: ['Move'],
    object: [
      { type: ['Note'] }
    ]
  }],
  content: async (act: Activity) => {
    console.log('SOMEONE MOVED A NOTE!', act);
  }
});