# Copyright 2023 Buf Technologies, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from buf.validate.internal import constraints as _constraints
from buf.validate.internal import extra_func
from buf.validate import expression_pb2
from google.protobuf import descriptor
from google.protobuf import message

Violations = expression_pb2.Violations


class Validator:
    _factory: _constraints.ConstraintFactory

    def __init__(self):
        self._factory = _constraints.ConstraintFactory(extra_func.EXTRA_FUNCS)

    def validate(
        self,
        message: message.Message,
        fail_fast: bool = False,
        result: Violations = None,
    ) -> Violations:
        ctx = _constraints.ConstraintContext(fail_fast=fail_fast, violations=result)
        self._validate_message(ctx, "", message)
        return ctx.violations

    def _validate_message(
        self,
        ctx: _constraints.ConstraintContext,
        field_path: str,
        msg: message.Message,
    ) -> None:
        for constraint in self._factory.get(msg.DESCRIPTOR):
            constraint.validate(ctx, field_path, msg)
            if ctx.done:
                return

        for field in msg.DESCRIPTOR.fields:
            if field.type != descriptor.FieldDescriptor.TYPE_MESSAGE:
                continue

            # TODO(afuller): Figure out why this segfault in a dynamic environment.
            sub_path = field.name if field_path == "" else f"{field_path}.{field.name}"
            if field.label == descriptor.FieldDescriptor.LABEL_REPEATED:
                value = getattr(msg, field.name)
                # for i, sub_msg in enumerate(value):
                #     self._validate_message(ctx, f"{sub_path}[{i}]", sub_msg)
                #     if ctx.done:
                #         return
            elif msg.HasField(field.name):
                value = getattr(msg, field.name)
                self._validate_message(ctx, sub_path, value)
                if ctx.done:
                    return


_validator = Validator()
validate = _validator.validate
