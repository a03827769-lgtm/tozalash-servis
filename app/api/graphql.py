import strawberry
from strawberry.fastapi import GraphQLRouter
from typing import List


@strawberry.type
class User:
    id: int
    name: str
    phone: str


@strawberry.type
class Order:
    id: int
    user_id: int
    status: str
    total_price: float


@strawberry.type
class Query:
    @strawberry.field
    def hello(self) -> str:
        return "Welcome to Tozalash Servis GraphQL API"

    @strawberry.field
    def users(self) -> List[User]:
        # Dummy data for now, will connect to DB later
        return [
            User(id=1, name="Ali", phone="+998901234567"),
            User(id=2, name="Vali", phone="+998909876543"),
        ]


schema = strawberry.Schema(query=Query)

graphql_app = GraphQLRouter(schema)
