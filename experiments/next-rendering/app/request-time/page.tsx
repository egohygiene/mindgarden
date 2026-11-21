import { connection } from "next/server";
import { RenderingPage } from "../../components/rendering-page";

export default async function Page() {
  await connection();
  return <RenderingPage mode="request-time" />;
}
