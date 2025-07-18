import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from ....models.thesis_model import ThesisModel
from src.schemas.thesis_schema import ThesisSchema


class ThesisRepository:

    @staticmethod
    async def upsert_thesis(session: AsyncSession, tesis: ThesisSchema):
        try:
            stmt = select(ThesisModel).where(ThesisModel.handle == tesis.handle)
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing is None:
                thesis = ThesisModel(**tesis.model_dump())
                session.add(thesis)
                await session.commit()
                print(f"✅ Insertado: {tesis.handle}")
                return True
            elif existing.is_vectorized:
                print(f"⏩ Ya procesado: {tesis.handle}")
                return False
            elif existing.download_url != tesis.download_url:
                existing.download_url = tesis.download_url
                existing.is_vectorized = False
                await session.commit()
                print(f"🔄 Actualizado URL: {tesis.handle}")
                return True
            else:
                print(f"ℹ️ Sin cambios: {tesis.handle}")
                return False

        except SQLAlchemyError as e:
            await session.rollback()
            print(f"❌ Error: {e}")
            return False

    @staticmethod
    async def get_all(session: AsyncSession):
        stmt = select(ThesisModel)
        result = await session.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_by_handle(session: AsyncSession, handle: str):
        stmt = select(ThesisModel).where(ThesisModel.handle == handle)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def delete_by_handle(session: AsyncSession, handle: str):
        thesis = await ThesisRepository.get_by_handle(session, handle)
        if thesis:
            await session.delete(thesis)
            await session.commit()
            print(f"🗑️ Eliminada: {handle}")
            return True
        else:
            print(f"❌ No encontrada: {handle}")
            return False

    @staticmethod
    async def mark_as_vectorized(session: AsyncSession, handle: str):
        try:
            thesis = await ThesisRepository.get_by_handle(session, handle)
            if thesis:
                if thesis.is_vectorized:
                    print(f"⏩ Ya estaba marcado como procesado: {handle}")
                    return False
                thesis.is_vectorized = True
                await session.commit()
                print(f"✅ Marcado como procesado: {handle}")
                return True
            else:
                print(f"❌ Tesis no encontrada: {handle}")
                return False
        except SQLAlchemyError as e:
            await session.rollback()
            print(f"❌ Error al marcar como procesado: {e}")
            return False
        
    @staticmethod
    async def get_non_vectorized_theses(session: AsyncSession):
        """
        Devuelve una lista de tesis que aún no han sido procesadas (vectorizadas).
        """
        try:
            stmt = select(ThesisModel).where(ThesisModel.is_vectorized == False)
            result = await session.execute(stmt)
            theses = result.scalars().all()
            print(f"📥 {len(theses)} tesis sin procesar encontradas.")
            return theses
        except SQLAlchemyError as e:
            print(f"❌ Error al obtener tesis sin procesar: {e}")
            return []
        
    @staticmethod
    async def delete_all(session: AsyncSession) -> bool:
        """
        Elimina todas las tesis de la base de datos.
        """
        try:
            num_deleted = await session.execute(
                ThesisModel.__table__.delete()
            )
            await session.commit()
            print(f"🗑️ Todas las tesis eliminadas.")
            return True
        except SQLAlchemyError as e:
            await session.rollback()
            print(f"❌ Error al eliminar todas las tesis: {e}")
            return False

    # @staticmethod
    # async def bulk_insert_theses(session: AsyncSession, theses: list[ThesisSchema]):
    #     try:
    #         # Convierte a diccionarios (ideal para bulk)
    #         mappings = [t.model_dump() for t in theses]
    #         print("Agregando tesis...")
    #         await session.execute(
    #             ThesisModel.__table__.insert().values(mappings)
    #         )
    #         await session.commit()
    #         print(f"✅ Se insertaron {len(mappings)} tesis nuevas.")
    #     except SQLAlchemyError as e:
    #         await session.rollback()
    #         print(f"❌ Error en inserción en bloque: {e}")


#*************************** Test ***************************
# async def test_thesis_repository():
#     async with AsyncSessionLocal() as session:
#         # Test upsert
#         dto = ThesisDto(
#             handle="123/123",
#             metadata_json={"title": "Test Thesis"},
#             original_name="test_thesis.pdf",
#             size_bytes=123456,
#             download_url="http://example.com/test_thesis_1.pdf",
#             checksum_md5="abc123",
#             is_processed=False
#         )
#         await ThesisRepository.upsert_thesis(session, dto)

# async def main():
#     async with AsyncSessionLocal() as session:
#         # Test upsert
#         dto1 = ThesisSchema(
#             handle="789/789",
#             metadata_json={"title": "Tesis de prueba 5"},
#             original_name_document="tesis_de_prueba5",
#             size_bytes_document=123456,
#             download_url="http://example.com/tesis_de_prueba5.pdf",
#             checksum_md5="tdp5",
#             is_processed=False
#         )
#         dto2 = ThesisSchema(
#             handle="10/10",
#             metadata_json={"title": "Tesis de prueba 6"},
#             original_name_document="tesis_de_prueba6",
#             size_bytes_document=123456,
#             download_url="https://repositorio.minciencias.gov.co/server/api/core/bitstreams/d8136985-e6e9-4a1e-93c8-bc8b43e185a7/content",
#             checksum_md5="tdp6",
#             is_processed=False
#         )
#         dto3 = ThesisSchema(
#             handle="11/11",
#             metadata_json={"title": "Tesis de prueba 7"},
#             original_name_document="tesis_de_prueba7",
#             size_bytes_document=123456,
#             download_url="",
#             checksum_md5="tdp7",
#             is_processed=False
#         )
#         # await ThesisRepository.upsert_thesis(session, dto1)
#         # await ThesisRepository.upsert_thesis(session, dto3)
#         # await ThesisRepository.upsert_thesis(session, dto2)

#         # await ThesisRepository.mark_as_processed(session, "123/123")
#         # await ThesisRepository.delete_all(session)
#         theses = await ThesisRepository.get_all(session)
#         for thesis in theses:
#             print(f"📘 Handle: {thesis.handle}, Procesada: {thesis.is_vectorized}, Metadatos:{thesis.metadata_json}, Url: {thesis.download_url}" )

#         print("cantidad de tesis", len(theses))


# if __name__ == "__main__":
#     asyncio.run(main())

#         # # Test get all
#         # theses = await ThesisRepository.get_all(session)
#         # print(f"Total theses: {len(theses)}")

#         # # Test get by handle
#         # thesis = await ThesisRepository.get_by_handle(session, "test_handle")
#         # print(f"Thesis found: {thesis}")

#         # Test delete by handle
#         # await ThesisRepository.delete_by_handle(session, "test_handle")
#         # thesis_after_delete = await ThesisRepository.get_by_handle(session, "test_handle")
#         # print(f"Thesis after delete: {thesis_after_delete}")