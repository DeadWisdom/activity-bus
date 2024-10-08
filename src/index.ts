import { processors as builtins } from "./builtins";
import { gather, gatherNodes, many, type Activity, type Tombstone } from "./model";


/// Processing ///////////
export async function process(act: Activity, raise?: boolean): Promise<Activity> {
  act.id = '/outbox/' + Math.random().toString(36).slice(2);

  try {
    await audit(act);
    await execute(act);
    await finalize(act);
    await deliver(act);
  } catch (e: any) {
    await terminate(act, e);
    if (raise) throw e;
  }

  return act;
}


/// Processing Steps ///////////
async function audit(act: Activity) {
  // Audits at the system level
  // console.debug("+ auditing", act.id);
}

async function execute(act: Activity) {
  // Runs the activity through the rules engine and produces side-effects
  // console.log("+ executing", act.id);

  for (let fn of builtins) {
    await fn(act);
  }
}

async function finalize(act: Activity) {
  // Finalizes any processing of the activity
  act.processed = new Date().toISOString();
  // console.log("+ finalzied", act.id);
}

async function deliver(act: Activity) {
  // Delivers the activity to inboxes of targets
  // For each target in cc, bcc, to, bto:
  //   - Deliver the activity to the target's inbox
  //   - If the target is a collection, deliver to all items in the collection
  //   - If the collection is really big, deliver it to a shared inbox
  let nodes = gatherNodes(act.to, act.bto, act.cc, act.bcc);
  // console.log("+ delivering to", nodes);
}


/// Error Handling ///////////
export class ProcessingError {
  summary: string[];

  constructor(summary: string | string[]) {
    this.summary = gather(summary);
  }
}

async function terminate(act: Activity, error?: ProcessingError | Error) {
  if (error instanceof ProcessingError) {
    act.result = gatherNodes(act.result, error);
  } else if (error instanceof Error) {
    act.result = gatherNodes(act.result, new ProcessingError(error.message));
  }

  act.originalType = act.type;
  act.type = ['Tombstone'];
  act.deleted = new Date().toISOString();
  return act as Tombstone;
}
