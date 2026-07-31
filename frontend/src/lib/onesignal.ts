type OneSignalSubscriptionState = {
  id?: string | null;
  optedIn?: boolean;
  token?: string | null;
};

type SubscriptionChange = {
  current: OneSignalSubscriptionState;
  previous: OneSignalSubscriptionState;
};

type OneSignalSdk = {
  init: (options: {
    appId: string;
    allowLocalhostAsSecureOrigin?: boolean;
  }) => Promise<void>;
  login: (externalId: string) => Promise<void>;
  logout: () => Promise<void>;
  Notifications: {
    isPushSupported: () => boolean;
  };
  User: {
    PushSubscription: {
      id: string | null;
      optedIn: boolean;
      optIn: () => Promise<void>;
      addEventListener: (
        event: "change",
        listener: (event: SubscriptionChange) => void,
      ) => void;
      removeEventListener: (
        event: "change",
        listener: (event: SubscriptionChange) => void,
      ) => void;
    };
  };
};

declare global {
  interface Window {
    OneSignalDeferred?: Array<
      (oneSignal: OneSignalSdk) => void | Promise<void>
    >;
  }
}

let initialized = false;

function withOneSignal<T>(
  callback: (oneSignal: OneSignalSdk) => Promise<T>,
): Promise<T> {
  return new Promise((resolve, reject) => {
    window.OneSignalDeferred = window.OneSignalDeferred || [];
    window.OneSignalDeferred.push(async (oneSignal) => {
      try {
        resolve(await callback(oneSignal));
      } catch (error) {
        reject(error);
      }
    });
  });
}

async function ensureInitialized(oneSignal: OneSignalSdk) {
  const appId = process.env.NEXT_PUBLIC_ONESIGNAL_APP_ID;
  if (!appId) throw new Error("OneSignal is not configured.");
  if (!initialized) {
    await oneSignal.init({
      appId,
      allowLocalhostAsSecureOrigin: true,
    });
    initialized = true;
  }
}

export async function subscribeBrowser(userId: number): Promise<string> {
  return withOneSignal(async (oneSignal) => {
    await ensureInitialized(oneSignal);
    if (!oneSignal.Notifications.isPushSupported()) {
      throw new Error("This browser does not support Web Push.");
    }
    await oneSignal.login(String(userId));
    await oneSignal.User.PushSubscription.optIn();

    const existing = oneSignal.User.PushSubscription.id;
    if (existing) return existing;

    return new Promise<string>((resolve, reject) => {
      const timeout = window.setTimeout(() => {
        oneSignal.User.PushSubscription.removeEventListener("change", listener);
        reject(new Error("The browser subscription was not ready. Please try again."));
      }, 15000);
      const listener = (event: SubscriptionChange) => {
        if (!event.current.id) return;
        window.clearTimeout(timeout);
        oneSignal.User.PushSubscription.removeEventListener("change", listener);
        resolve(event.current.id);
      };
      oneSignal.User.PushSubscription.addEventListener("change", listener);
    });
  });
}

export async function logoutOneSignal() {
  if (!process.env.NEXT_PUBLIC_ONESIGNAL_APP_ID) return;
  await withOneSignal(async (oneSignal) => {
    await ensureInitialized(oneSignal);
    await oneSignal.logout();
  });
}
