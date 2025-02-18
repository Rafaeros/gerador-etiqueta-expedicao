import aiohttp
import asyncio


async def fkapi_get_op_data_by_codigo(codigo_ordem_producao: str) -> str | None:
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"http://pcjiga-rafa:8090/api/v1/ordens_materiais/{codigo_ordem_producao}"
            ) as response:
                if response.status == 404:
                    return None

                if response.status == 500:
                    return None

                if response.ok:
                    return await response.text()
    except aiohttp.ClientConnectorError:
        return None


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    print(loop.run_until_complete(fkapi_get_op_data_by_codigo("223536")))
