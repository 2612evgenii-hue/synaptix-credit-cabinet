import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";
import {
  seed,
  type State,
  type Application,
  type Role,
  blank,
  now,
} from "./domain";
const KEY = "synaptix.frontend.v2";
function load(): State {
  try {
    const value = localStorage.getItem(KEY);
    if (value) {
      const s = JSON.parse(value);
      if (s.schema === 2 && Array.isArray(s.applications)) return s;
    }
  } catch {}
  return seed();
}
type Store = {
  state: State;
  error: string;
  update: (fn: (s: State) => State) => boolean;
  change: (id: string, fn: (a: Application) => Application) => boolean;
  login: (r: Role) => void;
  newApplication: (
    product?: "loan" | "line",
    amount?: number,
    months?: number,
    goal?: string,
    requestedDraw?: number,
  ) => string;
  reset: () => void;
};
const Context = createContext<Store | null>(null);
export function Provider({ children }: { children: ReactNode }) {
  const [state, setState] = useState(load);
  const [error, setError] = useState("");
  const update = useCallback(
    (fn: (s: State) => State) => {
      try {
        const next = fn(state);
        localStorage.setItem(KEY, JSON.stringify(next));
        setState(next);
        setError("");
        return true;
      } catch (e) {
        setError(e instanceof Error ? e.message : "Изменения не сохранились");
        return false;
      }
    },
    [state],
  );
  useEffect(() => {
    const sync = (e: StorageEvent) => {
      if (e.key === KEY) setState(load());
    };
    window.addEventListener("storage", sync);
    return () => window.removeEventListener("storage", sync);
  }, []);
  const change = (id: string, fn: (a: Application) => Application) =>
    update((s) => ({
      ...s,
      readNotifications: false,
      applications: s.applications.map((a) => (a.id === id ? fn(a) : a)),
    }));
  const login = (role: Role) => update((s) => ({ ...s, role }));
  const newApplication = (
    product: "loan" | "line" = "loan",
    amount = 1500000,
    months = 24,
    goal = "Закупка товара и материалов",
    requestedDraw?: number,
  ) => {
    const id = "АК-" + state.nextId;
    const ok = update((s) => ({
      ...s,
      role: s.role === "bank" || !s.role ? "director" : s.role,
      nextId: s.nextId + 1,
      applications: [
        { ...blank(id, product, amount, months, goal), requestedDraw },
        ...s.applications,
      ],
    }));
    return ok ? id : "";
  };
  const reset = () => {
    const fresh = seed();
    update(() => ({ ...fresh, role: state.role }));
  };
  return (
    <Context.Provider
      value={{ state, error, update, change, login, newApplication, reset }}
    >
      {children}
      {error && (
        <div role="alert" className="persistent-error">
          Изменения не сохранены. {error}
        </div>
      )}
    </Context.Provider>
  );
}
export function useStore() {
  const v = useContext(Context);
  if (!v) throw new Error("Provider required");
  return v;
}
export function useRoute() {
  const [route, set] = useState(() => location.hash.slice(1) || "/");
  useEffect(() => {
    const f = () => {
      set(location.hash.slice(1) || "/");
      window.scrollTo(0, 0);
    };
    window.addEventListener("hashchange", f);
    return () => window.removeEventListener("hashchange", f);
  }, []);
  return route;
}
export const go = (path: string) => {
  location.hash = path;
};
export function event(text: string, actor = "Клиент") {
  return { date: now(), text, actor };
}
