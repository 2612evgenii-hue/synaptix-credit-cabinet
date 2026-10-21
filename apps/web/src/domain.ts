// Browser-only scenario model. This is not the bank API or a credit decision engine.
export type Product = "loan" | "line";
export type Role = "director" | "accountant" | "bank";
export type Status =
  | "draft"
  | "review"
  | "needs_info"
  | "approved"
  | "alternative"
  | "rejected"
  | "signed"
  | "ready"
  | "issued"
  | "closed";
export type Doc = {
  id: string;
  name: string;
  kind: string;
  data: string;
  mime: string;
  status: "added" | "accepted";
  date: string;
};
export type Event = {
  date: string;
  text: string;
  actor: string;
  internal?: boolean;
};
export type Application = {
  id: string;
  company: string;
  inn: string;
  activity: string;
  address: string;
  product: Product;
  goal: string;
  requestedDraw?: number;
  requestDocCount?: number;
  amount: number;
  months: number;
  rate: number;
  revenue: string;
  expenses: string;
  debt: string;
  payment: string;
  comment: string;
  step: number;
  status: Status;
  docs: Doc[];
  history: Event[];
  request: string;
  owner: string;
  offerAmount?: number;
  offerMonths?: number;
  offerRate?: number;
  version: number;
  signedVersion?: number;
  clientReason: string;
  internalComment: string;
  drawn: number;
  repaid: number;
  tranches?: {
    id: string;
    amount: number;
    months: number;
    rate: number;
    repaid: number;
    date: string;
  }[];
  created: string;
};
export type SupportCase = {
  id: string;
  subject: string;
  text: string;
  answer: string;
  closed: boolean;
  date: string;
};
export type PlanEntry = {
  id: string;
  name: string;
  amount: number;
  date: string;
  type: "income" | "expense";
};
export type State = {
  schema: 2;
  role: Role | null;
  applications: Application[];
  support: SupportCase[];
  plan: PlanEntry[];
  planOpening?: number;
  topics: string[];
  readNotifications: boolean;
  nextId: number;
};
export const CATALOG = {
  loan: {
    name: "Кредит для бизнеса",
    min: 300000,
    max: 5000000,
    minMonths: 6,
    maxMonths: 36,
    rate: 16,
  },
  line: {
    name: "Возобновляемая кредитная линия",
    min: 500000,
    max: 10000000,
    minMonths: 3,
    maxMonths: 12,
    rate: 18,
  },
} as const;
export const STATUS: Record<
  Status,
  { label: string; tone: string; next: string }
> = {
  draft: { label: "Черновик", tone: "gray", next: "Продолжите заполнение" },
  review: {
    label: "На рассмотрении",
    tone: "blue",
    next: "Сейчас действий не требуется",
  },
  needs_info: {
    label: "Нужны сведения",
    tone: "orange",
    next: "Ответьте на запрос банка",
  },
  approved: {
    label: "Условия готовы",
    tone: "green",
    next: "Проверьте предложение",
  },
  alternative: {
    label: "Другие условия",
    tone: "orange",
    next: "Сравните с вашей заявкой",
  },
  rejected: { label: "Не одобрена", tone: "gray", next: "Посмотрите решение" },
  signed: {
    label: "Документы подписаны",
    tone: "blue",
    next: "Банк проверяет готовность к выдаче",
  },
  ready: {
    label: "Готово к выдаче",
    tone: "green",
    next: "Проверьте счёт и запросите выдачу",
  },
  issued: {
    label: "Действует",
    tone: "green",
    next: "Следите за графиком платежей",
  },
  closed: {
    label: "Закрыт",
    tone: "gray",
    next: "Документы и история доступны",
  },
};
export const money = (n: number) =>
  new Intl.NumberFormat("ru-RU", {
    style: "currency",
    currency: "RUB",
    maximumFractionDigits: 0,
  }).format(n);
export const moneyExact = (n: number) =>
  new Intl.NumberFormat("ru-RU", {
    style: "currency",
    currency: "RUB",
    minimumFractionDigits: 2,
  }).format(n);
export const dateLabel = (d: string) =>
  new Date(d).toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
export const uid = () => crypto.randomUUID();
export const now = () => new Date().toISOString();
export function schedule(
  amount: number,
  months: number,
  annualRate: number,
  start = "2026-10-21",
) {
  if (
    !Number.isFinite(amount) ||
    amount <= 0 ||
    !Number.isInteger(months) ||
    months < 1 ||
    months > 120 ||
    !Number.isFinite(annualRate) ||
    annualRate < 0
  )
    return [];
  const r = annualRate / 1200;
  const nominal =
    r === 0 ? amount / months : (amount * r) / (1 - Math.pow(1 + r, -months));
  let balance = Math.round(amount * 100);
  const rows = [];
  for (let i = 1; i <= months; i++) {
    const interest = Math.round(balance * r);
    const principal =
      i === months
        ? balance
        : Math.min(balance, Math.round(nominal * 100) - interest);
    const d = new Date(start + "T12:00:00");
    d.setMonth(d.getMonth() + i);
    rows.push({
      n: i,
      date: d.toISOString().slice(0, 10),
      principal: principal / 100,
      interest: interest / 100,
      total: (principal + interest) / 100,
      balance: (balance - principal) / 100,
    });
    balance -= principal;
  }
  return rows;
}
export function quote(amount: number, months: number, rate: number) {
  const rows = schedule(amount, months, rate);
  return {
    rows,
    payment: rows[0]?.total ?? 0,
    total: Math.round(rows.reduce((s, r) => s + r.total, 0) * 100) / 100,
    interest: Math.round(rows.reduce((s, r) => s + r.interest, 0) * 100) / 100,
  };
}
export function blank(
  id: string,
  product: Product = "loan",
  amount = 1500000,
  months = 24,
  goal = "Закупка товара и материалов",
): Application {
  return {
    id,
    company: "ООО «Маяк»",
    inn: "0000000000",
    activity: "Оптовая торговля",
    address: "Демо-город, улица Примерная, 1",
    product,
    goal,
    amount,
    months,
    rate: CATALOG[product].rate,
    revenue: "",
    expenses: "",
    debt: "",
    payment: "",
    comment: "",
    step: 0,
    status: "draft",
    docs: [],
    history: [{ date: now(), text: "Черновик создан", actor: "Клиент" }],
    request: "",
    owner: "",
    version: 1,
    clientReason: "",
    internalComment: "",
    drawn: 0,
    repaid: 0,
    created: now(),
  };
}
export function demoDocument(name = "Выписка за 6 месяцев.txt"): Doc {
  return {
    id: uid(),
    name,
    kind: "Выписка",
    mime: "text/plain",
    data: "ДЕМОНСТРАЦИОННЫЙ ДОКУМЕНТ\nООО «Маяк». ИНН 0000000000.\nСинтетический пример. Не является банковской выпиской.\nВыручка за 6 месяцев: 12 000 000 рублей.\nРасходы за 6 месяцев: 8 000 000 рублей.\nНикаких реальных операций или реквизитов.",
    status: "added",
    date: now(),
  };
}
export function seed(): State {
  const draft = blank("АК-1048");
  draft.step = 1;
  const review = blank("АК-1047", "loan", 2400000, 24, "Покупка оборудования");
  Object.assign(review, {
    company: "ООО «Маяк»",
    status: "review",
    step: 4,
    revenue: "12000000",
    expenses: "8000000",
    debt: "0",
    payment: "0",
    docs: [demoDocument()],
    history: [
      {
        date: now(),
        text: "Демо-заявка отправлена на рассмотрение",
        actor: "Руководитель",
      },
    ],
  });
  const activeLoan: Application = {
    ...review,
    id: "АК-1046",
    amount: 1500000,
    offerAmount: 1500000,
    offerMonths: 24,
    offerRate: 16,
    rate: 16,
    status: "issued",
    version: 2,
    signedVersion: 2,
    drawn: 1500000,
    history: [
      {
        date: now(),
        text: "Действующий кредит из синтетического набора",
        actor: "Демо-сценарий",
      },
    ],
  };
  const activeLine: Application = {
    ...review,
    id: "АК-1045",
    product: "line",
    goal: "Закупка товара и материалов",
    amount: 3000000,
    months: 6,
    rate: 18,
    offerAmount: 3000000,
    offerMonths: 6,
    offerRate: 18,
    status: "issued",
    version: 2,
    signedVersion: 2,
    drawn: 700000,
    requestedDraw: 700000,
    tranches: [
      {
        id: "001",
        amount: 700000,
        months: 6,
        rate: 18,
        repaid: 0,
        date: "2026-10-21T12:00:00Z",
      },
    ],
    history: [
      {
        date: now(),
        text: "Линия и первый транш из синтетического набора",
        actor: "Демо-сценарий",
      },
    ],
  };
  return {
    schema: 2,
    role: null,
    applications: [draft, review, activeLoan, activeLine],
    support: [],
    plan: [],
    topics: ["Закупки", "Документы"],
    readNotifications: false,
    nextId: 1049,
  };
}
export function validateApplication(a: Application): string[] {
  const errors: string[] = [];
  const c = CATALOG[a.product];
  if (!Number.isFinite(a.amount) || a.amount < c.min || a.amount > c.max)
    errors.push("Проверьте сумму финансирования");
  if (
    !Number.isInteger(a.months) ||
    a.months < c.minMonths ||
    a.months > c.maxMonths
  )
    errors.push("Проверьте срок");
  if (!a.company.trim()) errors.push("Укажите название компании");
  if (!/^(\d{10}|\d{12})$/.test(a.inn))
    errors.push("ИНН должен содержать 10 или 12 цифр");
  if (!a.activity.trim()) errors.push("Укажите вид деятельности");
  for (const [key, label] of [
    ["revenue", "выручку"],
    ["expenses", "расходы"],
    ["debt", "задолженность"],
    ["payment", "платежи"],
  ] as const) {
    if (a[key] === "" || !Number.isFinite(Number(a[key])) || Number(a[key]) < 0)
      errors.push("Укажите " + label + " за период");
  }
  if (!a.docs.length) errors.push("Добавьте документ из демо-набора");
  return errors;
}
const transitions: Record<Status, Status[]> = {
  draft: ["review"],
  review: ["needs_info", "approved", "alternative", "rejected"],
  needs_info: ["review"],
  approved: ["signed"],
  alternative: ["signed"],
  rejected: [],
  signed: ["ready"],
  ready: ["issued"],
  issued: ["closed"],
  closed: [],
};
export function transition(
  a: Application,
  to: Status,
  role: Role,
  text: string,
): Application {
  if (!transitions[a.status].includes(to))
    throw new Error("Действие недоступно на этом этапе");
  const bankActions = [
    "needs_info",
    "approved",
    "alternative",
    "rejected",
    "ready",
  ];
  if (bankActions.includes(to) && role !== "bank")
    throw new Error("Действие доступно сотруднику банка");
  if (!bankActions.includes(to) && role !== "director")
    throw new Error("Действие доступно руководителю");
  if (to === "review" && a.status === "draft" && validateApplication(a).length)
    throw new Error("Проверьте обязательные сведения");
  if (to === "signed" && a.offerAmount === undefined)
    throw new Error("Предложение не сформировано");
  if (to === "ready" && a.signedVersion !== a.version)
    throw new Error("Нужна подпись текущей версии");
  return {
    ...a,
    status: to,
    history: [
      ...a.history,
      {
        date: now(),
        text,
        actor: role === "bank" ? "Сотрудник банка" : "Руководитель",
      },
    ],
  };
}
export function terms(a: Application) {
  return {
    amount: a.offerAmount ?? a.amount,
    months: a.offerMonths ?? a.months,
    rate: a.offerRate ?? a.rate,
  };
}

export function contractDocument(a: Application): Doc {
  const t = terms(a);
  return {
    id: "contract-" + a.id,
    name: "Демо-договор " + a.id + ".txt",
    kind: "Договор",
    mime: "text/plain",
    status: a.signedVersion === a.version ? "accepted" : "added",
    date: a.created,
    data: `ДЕМОНСТРАЦИОННЫЙ ДОКУМЕНТ
Не является кредитным договором.
Заявка ${a.id}, версия ${a.version}
Компания: ${a.company}
Продукт: ${CATALOG[a.product].name}
Сумма / лимит: ${money(t.amount)}
${a.product === "line" ? "Срок первого транша" : "Срок кредита"}: ${t.months} месяцев${a.product === "line" ? "\nСрок линии: 24 месяца" : ""}
Ставка для демонстрации: ${t.rate}% годовых
Комиссии и услуги: 0 рублей
Подпись имитируется. Деньги не выдаются.`,
  };
}
