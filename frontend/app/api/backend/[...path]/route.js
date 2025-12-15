import axios from "axios";

export async function POST(req, { params }) {
  const body = await req.json();
  const url = `${process.env.NEXT_PUBLIC_BACKEND_URL}/${params.path.join("/")}`;

  const response = await axios.post(url, body);

  return Response.json(response.data);
}
