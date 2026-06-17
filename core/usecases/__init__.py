"""
Application use cases (write orchestration).

Default DRF flow keeps simple writes in serializers. Add modules here when a write
operation needs transaction orchestration across multiple entities, reuse from
background tasks or management commands, or business rules that no longer fit a
single serializer cleanly.

Layout:
  usecases/<entity>.py       entity-specific flows (for example checkout.place_order)
  usecases/common/           cross-cutting orchestration shared by multiple features

Call flow when used:
  viewset/serializer -> usecase -> service -> model
"""
