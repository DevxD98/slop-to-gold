export const ROUTES = ["/", "/users", "/settings"] as const;
export type Route = (typeof ROUTES)[number];
